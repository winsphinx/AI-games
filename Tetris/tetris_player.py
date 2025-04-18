import tkinter as tk
from tetris import Tetris  # Ensure tetris.py is in the same directory


class Player(Tetris):
    """
    An AI player that inherits from the Tetris class,
    It will automatically play the game to achieve a high score.
    """

    def __init__(self, master):
        super().__init__(master, auto_restart=True)  # Pass auto_restart=True
        self.ai_move_time = 50  # Time interval between AI decisions (milliseconds)
        self.binds_enabled = False  # Disable key bindings for human player
        self.master.title("Tetris AI Player")  # Update window title

        # AI state variables
        self.best_move = None  # Store the best move target {'rotation_target_state': int, 'x': int, 'score': float}
        self.current_rotation_count = (
            0  # Track the current rotation state of the block (0-3)
        )

        # Start AI loop
        self.master.after(self.ai_move_time, self.ai_loop)

    # --- Override base class methods to adapt to AI ---

    def bind_keys(self):
        """Disable key bindings"""
        pass

    def new_shape(self):
        """Reset AI state when a new block appears"""
        super().new_shape()
        # Reset AI target and rotation count for new block
        self.best_move = None
        self.current_rotation_count = 0
        # Note: Do not call ai_move() immediately here, let ai_loop handle it to avoid potential performance issues

    def rotate_shape(self) -> None:
        """
        Rotate the current shape with wall kick attempts.
        Updates rotation count and handles collisions.

        Implements basic wall kick by trying to shift left/right when rotation fails.
        """
        if not self.game_running or not self.current_shape:
            return

        old_state = {
            "shape": [row[:] for row in self.current_shape],
            "x": self.current_x,
            "rotation": self.current_rotation_count,
        }

        # Try rotation
        try:
            self.current_shape = [
                list(reversed(col)) for col in zip(*self.current_shape)
            ]
        except IndexError:
            return

        # Check collision and attempt wall kicks
        if self.check_collision():
            for dx in [1, -2, 2, -1]:  # Try right, then left, then wider kicks
                self.current_x += dx
                if not self.check_collision():
                    self.current_rotation_count = (self.current_rotation_count + 1) % 4
                    return
                self.current_x -= dx  # Revert if kick failed

            # All kicks failed - restore original state
            self.current_shape = old_state["shape"]
            self.current_x = old_state["x"]
        else:
            # Rotation successful
            self.current_rotation_count = (self.current_rotation_count + 1) % 4

    def move_down(self) -> bool:
        """
        Move the current shape down one unit.

        Returns:
            bool: True if the block was placed (or game over), False otherwise
        """
        if not self.game_running:
            return False

        self.current_y += 1
        if not self.check_collision():
            return False  # Block not placed yet

        # Block hit something - place it
        self.current_y -= 1
        self.place_shape()

        if self.game_running:
            self.new_shape()
            if self.check_collision():
                self.game_over()

        return True  # Block was placed

    def drop_shape(self):
        """Override fast drop logic"""
        if not self.game_running:
            return

        # Continuously move down until collision
        while not self.check_collision():
            self.current_y += 1
        # Step back one step
        self.current_y -= 1
        self.place_shape()
        if self.game_running:
            self.new_shape()  # Get new block and reset AI state
            if self.check_collision():
                self.game_over()
        # After fast drop, AI needs to immediately calculate target for new block
        self.best_move = None

    # --- AI Core Logic ---

    def ai_loop(self) -> None:
        """Optimized AI decision loop with better state management"""
        if not self.game_running:
            return

        current_piece = self.current_shape

        # Calculate move only if none exists or piece has changed
        if self.best_move is None or self.current_shape != current_piece:
            self.ai_move()

        # Execute best move if available
        if self.best_move:
            target_rot = self.best_move["rotation_target_state"]
            target_x = self.best_move["x"]

            # Rotation phase
            if self.current_rotation_count != target_rot:
                self.rotate_shape()
                # If rotation failed, recalculate
                if self.current_rotation_count != target_rot:
                    self.best_move = None

            # Movement phase
            elif self.current_x != target_x:
                direction = 1 if target_x > self.current_x else -1
                self.move_sideways(direction)

            # Drop phase
            else:
                placed = self.move_down()
                # If block placed, new_shape() was called which resets best_move

        # Fallback: force move down if no action taken
        elif self.game_running:
            self.move_down()

        # Schedule next iteration if game still running
        if self.game_running:
            self.master.after(self.ai_move_time, self.ai_loop)

    def ai_move(self) -> None:
        """
        Calculate and set the best move for the current block.

        Evaluates all possible moves and selects the one with highest score.
        If no valid moves found, sets best_move to None as fallback.
        """
        if not self.current_shape or not self.game_running:
            self.best_move = None
            return

        possible_moves = self.get_possible_moves()
        self.best_move = (
            max(possible_moves, key=lambda m: m["score"]) if possible_moves else None
        )

    def get_possible_moves(self) -> list[dict]:
        """
        Generate all possible final placement positions for the current block and evaluate them.
        Optimized to reduce nested loops and improve performance by caching shape properties.

        Returns:
            list[dict]: Each element contains move information:
                {'rotation_target_state': int, 'x': int, 'score': float}
        """
        if not self.current_shape:
            return []

        possible_moves = []
        initial_rotation = self.current_rotation_count
        current_shape = self.current_shape

        # Pre-calculate shape properties for all rotations
        shape_props = self._precalculate_shape_properties(
            current_shape, initial_rotation
        )

        # Evaluate each possible move
        for prop in shape_props:
            rotated = prop["rotated"]
            rot_state = prop["rot_state"]

            for x_pos in range(prop["min_x"], prop["max_x"] + 1):
                temp_x = x_pos
                # Check if the starting position overlaps with existing blocks (at the top)
                start_blocked = self._check_start_position_blocked(rotated, temp_x)
                if start_blocked:
                    continue  # Starting position blocked, cannot place

                # Simulate block drop to find final y position
                sim_y = self._simulate_block_drop(rotated, temp_x)

                # Skip if the block would cause game over
                if self._check_game_over_potential(rotated, temp_x, sim_y):
                    continue

                # Create simulated board state after placement
                temp_grid = self._create_simulated_board(rotated, temp_x, sim_y)

                # Simulate clearing rows on the simulated board
                final_sim_grid, lines_cleared_in_sim = self._simulate_row_clearing(
                    temp_grid
                )

                # Evaluate the score of the final simulated board
                score = self.evaluate_board_state(final_sim_grid, lines_cleared_in_sim)

                # Store this move and its score
                possible_moves.append(
                    {"rotation_target_state": rot_state, "x": x_pos, "score": score}
                )

        return possible_moves

    def _precalculate_shape_properties(
        self, current_shape: list[list[int]], initial_rotation: int
    ) -> list[dict]:
        """Pre-calculate properties for all possible rotations of the current shape."""
        shape_props = []
        for rot_state in range(4):
            rotations = (rot_state - initial_rotation + 4) % 4
            try:
                rotated = current_shape
                for _ in range(rotations):
                    rotated = [list(reversed(col)) for col in zip(*rotated)]

                if not rotated or not rotated[0]:
                    continue

                # Calculate min/max x positions
                cells = [
                    (x, y)
                    for y, row in enumerate(rotated)
                    for x, cell in enumerate(row)
                    if cell
                ]
                if not cells:
                    continue

                min_x = min(x for x, _ in cells)
                max_x = max(x for x, _ in cells)
                min_grid_x = -min_x
                max_grid_x = self.grid_width - 1 - max_x

                shape_props.append(
                    {
                        "rotated": rotated,
                        "rot_state": rot_state,
                        "min_x": min_grid_x,
                        "max_x": max_grid_x,
                    }
                )
            except IndexError:
                continue
        return shape_props

    def _check_start_position_blocked(
        self, rotated: list[list[int]], temp_x: int
    ) -> bool:
        """Check if the starting position overlaps with existing blocks at the top."""
        for y, row in enumerate(rotated):
            for x, cell in enumerate(row):
                if cell:
                    check_x = temp_x + x
                    check_y = 0 + y  # Check position near the top
                    if (
                        0 <= check_y < self.grid_height
                        and 0 <= check_x < self.grid_width
                    ):
                        if self.grid[check_y][check_x]:
                            return True
            if True in [
                self.grid[0 + y][temp_x + x]
                for x, cell in enumerate(row)
                if cell and 0 <= temp_x + x < self.grid_width
            ]:
                return True
        return False

    def _simulate_block_drop(self, rotated: list[list[int]], temp_x: int) -> int:
        """Simulate dropping the block to find its final y position."""
        sim_y = 0
        while True:
            collision = False
            for y, row in enumerate(rotated):
                for x, cell in enumerate(row):
                    if cell:
                        next_x = temp_x + x
                        next_y = sim_y + y + 1  # Check position below
                        if (
                            next_x < 0
                            or next_x >= self.grid_width
                            or next_y >= self.grid_height
                            or (next_y >= 0 and self.grid[next_y][next_x])
                        ):
                            collision = True
                            break
                if collision:
                    break
            if collision:
                break  # sim_y is the final Y coordinate
            sim_y += 1
        return sim_y

    def _check_game_over_potential(
        self, rotated: list[list[int]], temp_x: int, sim_y: int
    ) -> bool:
        """Check if placing the block would cause a game over."""
        game_over_potential = False
        for y, row in enumerate(rotated):
            for x, cell in enumerate(row):
                if cell:
                    place_x = temp_x + x
                    place_y = sim_y + y
                    if (
                        0 <= place_y < self.grid_height
                        and 0 <= place_x < self.grid_width
                    ):
                        if self.grid[place_y][place_x]:  # Overlap should not happen
                            game_over_potential = True
                            break
                    else:
                        # If the block is partially or fully out of bounds (only possible when sim_y < 0)
                        if place_y < 0:
                            game_over_potential = True
                            break
            if game_over_potential:
                break
        return game_over_potential

    def _create_simulated_board(
        self, rotated: list[list[int]], temp_x: int, sim_y: int
    ) -> list[list[int]]:
        """Create a simulated board state after placing the block."""
        temp_grid = [row[:] for row in self.grid]
        for y, row in enumerate(rotated):
            for x, cell in enumerate(row):
                if cell:
                    place_x = temp_x + x
                    place_y = sim_y + y
                    if (
                        0 <= place_y < self.grid_height
                        and 0 <= place_x < self.grid_width
                    ):
                        temp_grid[place_y][
                            place_x
                        ] = 1  # Use 1 to indicate block presence
        return temp_grid

    def _simulate_row_clearing(
        self, temp_grid: list[list[int]]
    ) -> tuple[list[list[int]], int]:
        """Simulate clearing rows on the simulated board and return the updated grid and cleared lines count."""
        lines_cleared_in_sim = 0
        rows_to_keep = []
        for r in range(self.grid_height - 1, -1, -1):  # Check from bottom to top
            is_full = all(temp_grid[r])
            if not is_full:
                rows_to_keep.insert(0, temp_grid[r])
            else:
                lines_cleared_in_sim += 1

        # Create the final simulated board (add empty rows at the top)
        final_sim_grid = [
            [0] * self.grid_width for _ in range(lines_cleared_in_sim)
        ] + rows_to_keep
        return final_sim_grid, lines_cleared_in_sim

    # --- Board Evaluation Function ---

    def evaluate_board_state(self, grid: list[list[int]], lines_cleared: int) -> float:
        """
        Evaluate the board state using optimized heuristic scoring.

        Args:
            grid: The board state matrix (1 = block, 0 = empty)
            lines_cleared: Number of lines cleared in this move

        Returns:
            float: Heuristic score (higher is better)
        """
        # Updated weights based on testing
        WEIGHTS = {
            "height": -0.7,  # Prefer lower stacks
            "lines": 4.0,  # Reward line clears
            "holes": -1.7,  # Penalize holes severely
            "bumpiness": -0.3,  # Slightly prefer smooth surfaces
            "wells": 0.2,  # Reward potential well formations
        }

        # Calculate metrics in single pass where possible
        heights = [0] * self.grid_width
        holes = 0
        well_depths = [0] * (self.grid_width - 2)

        for x in range(self.grid_width):
            col_height = 0
            found_block = False
            for y in range(self.grid_height):
                if y < len(grid) and x < len(grid[y]) and grid[y][x]:
                    col_height = self.grid_height - y
                    found_block = True
                    break
            heights[x] = col_height

            # Count holes in this column
            if found_block:
                for y in range(self.grid_height - col_height + 1, self.grid_height):
                    if y < len(grid) and x < len(grid[y]) and not grid[y][x]:
                        holes += 1

        # Calculate bumpiness and well depths
        bumpiness = 0
        for i in range(self.grid_width - 1):
            diff = abs(heights[i] - heights[i + 1])
            bumpiness += diff

            # Detect wells (columns lower than both neighbors)
            if 0 < i < self.grid_width - 2:
                if heights[i] < heights[i - 1] and heights[i] < heights[i + 1]:
                    well_depths[i - 1] = (
                        min(heights[i - 1], heights[i + 1]) - heights[i]
                    )

        agg_height = sum(heights)
        well_score = sum(well_depths)

        # Calculate final score
        score = (
            WEIGHTS["height"] * agg_height
            + WEIGHTS["lines"] * (lines_cleared**2)
            + WEIGHTS["holes"] * holes
            + WEIGHTS["bumpiness"] * bumpiness
            + WEIGHTS["wells"] * well_score
        )

        return score

    # --- Helper methods for evaluation metrics ---

    # Removed unused helper methods since evaluate_board_state() now calculates
    # all metrics in a single pass

    # --- Game start method ---
    @classmethod
    def run_game(cls):
        """Create Tkinter window and run the AI player"""
        root = tk.Tk()
        player = cls(
            root
        )  # Create Player instance, it will start the game automatically
        root.mainloop()


# --- Main program entry ---
if __name__ == "__main__":
    Player.run_game()
