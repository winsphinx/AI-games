import tkinter as tk
import random


class Tetris:
    """Main class for Tetris game"""

    def __init__(self, master: tk.Tk, auto_restart: bool = False) -> None:
        """Initialize the game

        Args:
            master: tkinter root window
            auto_restart: whether to auto-restart after game over
        """
        self.master = master
        master.title("Tetris")
        self.auto_restart = auto_restart  # Store the flag

        self.width = 300
        self.height = 600
        self.square_size = 30
        self.grid_width = self.width // self.square_size
        self.grid_height = self.height // self.square_size

        self.canvas = tk.Canvas(
            master, width=self.width, height=self.height, bg="black"
        )
        self.canvas.pack()

        self.next_canvas = tk.Canvas(
            master, width=self.width, height=self.square_size * 4, bg="black"
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.next_canvas.grid(row=0, column=0, sticky="ew")
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.grid = [
            [0 for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]  # Avoid potential reference issues with list multiplication
        self.shapes = [  # Shapes are now tuples for immutability
            ((1, 1, 1, 1),),
            ((1, 0, 0), (1, 1, 1)),
            ((0, 0, 1), (1, 1, 1)),
            ((1, 1), (1, 1)),
            ((0, 1, 1), (1, 1, 0)),
            ((1, 1, 1), (0, 1, 0)),
            ((1, 1, 0), (0, 1, 1)),
        ]
        self.colors = ["cyan", "blue", "orange", "yellow", "green", "purple", "red"]
        self.current_shape = None
        self.current_shape_color = None
        self.current_x = 0
        self.current_y = 0

        self.next_shape = None
        self.next_shape_color = None

        self.score = 0
        self.score_label = tk.Label(
            self.master, text="Score: 0", fg="white", bg="black", font=("Helvetica", 16)
        )
        self.score_label.grid(row=2, column=0, sticky="ew")

        self.game_running = True
        self.new_shape()
        self.bind_keys()
        self.game_loop()

    def bind_keys(self) -> None:
        """Bind keyboard key events"""
        key_bindings = {
            "<Left>": lambda e: self.move_sideways(-1),
            "<Right>": lambda e: self.move_sideways(1),
            "<Down>": lambda e: self.move_down(),
            "<Up>": lambda e: self.rotate_shape(),
            "<space>": lambda e: self.drop_shape(),
        }
        for key, func in key_bindings.items():
            self.master.bind(key, func)

    def new_shape(self) -> None:
        """Generate new current shape and next shape"""

        def get_random_shape() -> tuple[int, tuple[tuple[int, ...], ...], str]:
            """Get random shape info"""
            index = random.randint(0, len(self.shapes) - 1)
            return index, self.shapes[index], self.colors[index]

        # Generate current shape
        current_idx, current_shape, current_color = get_random_shape()
        self.current_shape = current_shape
        self.current_shape_color = current_color
        self.current_x = self.grid_width // 2 - len(current_shape[0]) // 2
        self.current_y = 0

        # Generate next shape
        next_idx, next_shape, next_color = get_random_shape()
        self.next_shape = next_shape
        self.next_shape_color = next_color

    def draw_shape(self) -> None:
        """Draw the currently moving shape"""
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    self._draw_square(
                        x=self.current_x + x,
                        y=self.current_y + y,
                        color=self.current_shape_color,
                        tags="grid_and_shape",
                    )

    def draw_next_shape(self):
        if self.next_shape is not None:
            next_shape = self.next_shape
            next_shape_color = self.next_shape_color
            next_canvas = self.next_canvas
            next_canvas.delete("all")

            # Calculate center offset
            max_width = 0
            for row in next_shape:
                max_width = max(max_width, len(row))

            offset_x = (self.width - max_width * self.square_size) // 2
            offset_y = (
                self.square_size * 4 - len(next_shape) * self.square_size
            ) // 2  # Ensure integer division for correct centering

            for y, row in enumerate(next_shape):
                for x, cell in enumerate(row):
                    if cell:
                        x_pos = offset_x + x * self.square_size
                        y_pos = offset_y + y * self.square_size
                        next_canvas.create_rectangle(
                            x_pos,
                            y_pos,
                            x_pos + self.square_size,
                            y_pos + self.square_size,
                            fill=next_shape_color,
                            outline="black",
                        )

    def move_sideways(self, direction: int) -> None:
        """Move shape horizontally

        Args:
            direction: move direction (-1 left, 1 right)
        """
        self.current_x += direction
        if self.check_collision():
            self.current_x -= direction  # Revert if collision

    def move_down(self) -> None:
        """Move shape down, lock it and generate new shape if bottom reached"""
        self.current_y += 1
        if self.check_collision():
            self.current_y -= 1  # Revert
            self.place_shape()  # Lock current shape
            self.new_shape()  # Generate new shape
            if self.check_collision():  # Check game over
                self.game_over()

    def drop_shape(self) -> None:
        """Drop current shape to bottom instantly"""
        while not self.check_collision():
            self.current_y += 1
        self.current_y -= 1  # Revert to pre-collision position
        self.place_shape()  # Lock the shape
        self.new_shape()  # Generate new shape
        if self.check_collision():  # Check game over
            self.game_over()

    def rotate_shape(self) -> None:
        """Rotate current shape (except O-shape)"""
        # O-shape doesn't need rotation
        if self.current_shape == self.shapes[3]:
            return

        # Rotate shape (transpose then reverse each column)
        rotated_shape = [list(reversed(col)) for col in zip(*self.current_shape)]
        old_shape = self.current_shape
        self.current_shape = rotated_shape

        # Revert if collision after rotation
        if self.check_collision():
            self.current_shape = old_shape

    def check_collision(self) -> bool:
        """Check if current shape collides with boundaries or locked shapes

        Returns:
            bool: whether collision occurred
        """
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.current_x + x
                    grid_y = self.current_y + y

                    # Check boundary collision
                    if (
                        grid_x < 0
                        or grid_x >= self.grid_width
                        or grid_y >= self.grid_height
                    ):
                        return True

                    # Check collision with locked shapes
                    if grid_y >= 0 and self.grid[grid_y][grid_x]:
                        return True
        return False

    def place_shape(self) -> None:
        """Lock current shape to grid and clear completed lines"""
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current_y + y][
                        self.current_x + x
                    ] = self.current_shape_color
        self.clear_lines()  # Check and clear completed lines

    def clear_lines(self) -> None:
        """Clear filled lines and update score"""
        new_grid = []
        lines_cleared = 0

        # Filter unfilled lines
        for y in range(self.grid_height):
            if not all(self.grid[y]):
                new_grid.append(self.grid[y])
            else:
                lines_cleared += 1

        # Add empty lines at top
        while len(new_grid) < self.grid_height:
            new_grid.insert(0, [0] * self.grid_width)

        self.grid = new_grid

        # Update score
        if lines_cleared > 0:
            self.update_score(lines_cleared)

    def update_score(self, lines_cleared: int) -> None:
        """Update score

        Args:
            lines_cleared: number of lines cleared this time
        """
        score_table = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += score_table.get(lines_cleared, 0)
        self.score_label.config(text=f"Score: {self.score}")

    def game_over(self) -> None:
        """Handle game over logic"""
        if self.auto_restart:
            self.restart_game()
        else:
            self._show_game_over_text()
            self.game_running = False

    def _show_game_over_text(self) -> None:
        """Show game over text"""
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text="Game Over",
            fill="white",
            font=("Helvetica", 30),
            tags="game_over_text",
        )

    def restart_game(self):
        """Reset game state to start a new game"""
        # Clear possible "Game Over" text
        self.canvas.delete("game_over_text")
        # Reset the grid
        self.grid = [[0] * self.grid_width for _ in range(self.grid_height)]
        # Reset the score
        self.score = 0
        self.score_label.config(text=f"Score: {self.score}")
        # Reset the next shape (to avoid retaining old ones)
        self.next_shape = None
        self.next_shape_color = None
        # Generate a new shape
        self.new_shape()
        # Ensure game state is running
        self.game_running = True

    def draw_grid(self) -> None:
        """Draw locked shapes grid"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x]:
                    self._draw_square(
                        x=x, y=y, color=self.grid[y][x], tags="grid_and_shape"
                    )

    def _draw_square(self, x: int, y: int, color: str, tags: str = "") -> None:
        """Draw single square

        Args:
            x: grid x coordinate
            y: grid y coordinate
            color: square color
            tags: canvas tags
        """
        x_pos = x * self.square_size
        y_pos = y * self.square_size
        self.canvas.create_rectangle(
            x_pos,
            y_pos,
            x_pos + self.square_size,
            y_pos + self.square_size,
            fill=color,
            outline="black",
            tags=tags,
        )

    def game_loop(self) -> None:
        """Main game loop"""
        if not self.game_running:
            return

        self.canvas.delete("grid_and_shape")
        self.draw_next_shape()

        self.move_down()

        self.draw_grid()
        self.draw_shape()

        # Adjust speed dynamically based on score
        base_speed = 500
        min_speed = 100
        speed_reduction = (self.score // 1000) * 50
        speed = max(min_speed, base_speed - speed_reduction)

        self.master.after(speed, self.game_loop)


if __name__ == "__main__":
    root = tk.Tk()
    tetris = Tetris(root)
    root.mainloop()
