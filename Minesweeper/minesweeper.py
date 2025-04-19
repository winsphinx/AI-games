import tkinter as tk
import random
import tkinter.messagebox as messagebox
from typing import Dict, Set, Tuple, List, Optional, Callable


class Minesweeper:
    # Color mapping for adjacent mine counts
    NUMBER_COLORS = {
        1: "blue",
        2: "green",
        3: "red",
        4: "purple",
        5: "maroon",
        6: "turquoise",
        7: "black",
        8: "gray",
    }

    def __init__(
        self, master: tk.Tk, rows: int = 10, cols: int = 10, mines: int = 10
    ) -> None:
        """Initialize the Minesweeper game

        Args:
            master: The root tkinter window
            rows: Number of rows in the game grid (minimum 5, maximum 30)
            cols: Number of columns in the game grid (minimum 5, maximum 30)
            mines: Number of mines to place (minimum 1, maximum rows*cols-1)

        Raises:
            ValueError: If invalid grid dimensions or mine count are provided
        """
        # Validate game configuration
        if rows < 5 or rows > 30 or cols < 5 or cols > 30:
            raise ValueError("Grid dimensions must be between 5x5 and 30x30")
        if mines < 1 or mines >= rows * cols:
            raise ValueError(f"Mine count must be between 1 and {rows*cols-1}")
        self.master = master
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.on_restart_callback = None  # Add callback attribute
        self.show_messages = True  # Control whether to show message boxes

        self.master.title("Minesweeper")

        # Status Bar Frame
        self.status_frame = tk.Frame(self.master, bd=1, relief=tk.SUNKEN)
        self.status_label = tk.Label(self.status_frame, text="", width=30)
        self.status_label.pack(side=tk.LEFT, padx=5)
        # Add Restart Button
        self.restart_button = tk.Button(
            self.status_frame, text="Restart", command=self.restart_game, width=10
        )
        self.restart_button.pack(side=tk.RIGHT, padx=5)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Game Frame
        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)  # Add padding to the game frame

        self.buttons = {}
        self.mine_locations = set()
        self.flags = 0
        self.cells_revealed = 0
        self.game_over = False

        self.start_game()  # Initial game setup

    def start_game(self) -> None:
        """Initialize or reset the game state and UI"""
        # Clear previous game widgets if any
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Reset game state
        self.buttons: Dict[Tuple[int, int], tk.Button] = {}
        self.mine_locations: Set[Tuple[int, int]] = set()
        self.flags = 0
        self.cells_revealed = 0
        self.game_over = False

        # Setup new game
        self.create_widgets()
        self.place_mines()
        self.calculate_adjacent_mines()
        self.update_status()  # Initial status update

    def restart_game(self) -> None:
        """Restart the game by resetting all state and UI

        Also calls the registered restart callback if one exists
        """
        self.start_game()
        if self.on_restart_callback:
            self.on_restart_callback()

    def create_widgets(self) -> None:
        """Create the game grid UI with buttons for each cell"""
        # Create button grid
        for r in range(self.rows):
            for c in range(self.cols):
                # Adjust button size for a more square look
                button = tk.Button(
                    self.frame,
                    width=2,
                    height=1,
                    font=("Consolas", 16),
                    bg="lightgray",
                    activebackground="darkgray",
                    activeforeground="white",
                    padx=2,
                    pady=2,
                    command=lambda r=r, c=c: self.on_click(r, c),
                )
                button.bind(
                    "<Button-3>", lambda e, r=r, c=c: self.on_right_click(r, c)
                )  # Bind right-click
                button.grid(row=r, column=c)
                self.buttons[(r, c)] = button

    def place_mines(self) -> None:
        """Randomly place mines on the game board"""
        # Randomly place mines
        count = 0
        while count < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) not in self.mine_locations:
                self.mine_locations.add((r, c))
                count += 1

    def calculate_adjacent_mines(self) -> None:
        """Calculate and store the number of adjacent mines for each cell"""
        # Calculate the number of mines around each cell
        self.adjacent_mines = {}
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mine_locations:
                    self.adjacent_mines[(r, c)] = "M"  # M for mine
                    continue

                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < self.rows
                            and 0 <= nc < self.cols
                            and (nr, nc) in self.mine_locations
                        ):
                            count += 1
                self.adjacent_mines[(r, c)] = count

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get valid neighbor coordinates for a given cell

        Args:
            r: Row index
            c: Column index

        Returns:
            List of (row, col) tuples for valid neighbors
        """
        # Get neighbor cells
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def reveal_cell(self, r: int, c: int) -> None:
        """Reveal a cell and its neighbors (iterative implementation)"""
        if (
            self.game_over
            or (r, c) not in self.buttons
            or self.buttons[(r, c)]["state"] == tk.DISABLED
        ):
            return

        # Use a stack for iterative flood fill instead of recursion
        stack = [(r, c)]
        while stack:
            current_r, current_c = stack.pop()
            button = self.buttons[(current_r, current_c)]

            # Skip if already revealed or flagged
            if button["state"] == tk.DISABLED or button["text"] == "🚩":
                continue

            button.config(state=tk.DISABLED, relief=tk.SUNKEN, bg="darkgray")
            self.cells_revealed += 1

            adjacent_count = self.adjacent_mines[(current_r, current_c)]

            if adjacent_count > 0:
                button.config(text=str(adjacent_count))
                button.config(
                    disabledforeground=self.NUMBER_COLORS.get(adjacent_count, "black")
                )
            else:
                # Add neighbors to stack if they are valid for revealing
                for nr, nc in self.get_neighbors(current_r, current_c):
                    if (nr, nc) in self.buttons:
                        neighbor_button = self.buttons[(nr, nc)]
                        if (
                            neighbor_button["state"] == tk.NORMAL
                            and neighbor_button["text"] != "🚩"
                        ):
                            stack.append((nr, nc))

        # Check win condition
        if (
            not self.game_over
            and self.cells_revealed == self.rows * self.cols - self.mines
        ):
            self.win_game()

    def on_click(self, r: int, c: int) -> None:
        """Handle left-click events on game cells

        Args:
            r: Row index of clicked cell
            c: Column index of clicked cell
        """
        # Left-click event
        if self.game_over:
            return

        button = self.buttons[(r, c)]
        if (
            button["state"] == tk.DISABLED or button["text"] == "🚩"
        ):  # Do nothing if already revealed or flagged
            return

        if (r, c) in self.mine_locations:
            self.lose_game(r, c)  # Pass the clicked mine location
        else:
            self.reveal_cell(r, c)

    def on_right_click(self, r: int, c: int) -> None:
        """Handle right-click events (flag/unflag) on game cells

        Args:
            r: Row index of clicked cell
            c: Column index of clicked cell
        """
        # Right-click event (flag/unflag)
        if self.game_over:
            return

        button = self.buttons[(r, c)]
        if button["state"] == tk.DISABLED:  # Cannot flag revealed cells
            return

        if button["text"] == "":
            if self.flags < self.mines:
                button.config(text="🚩", fg="red")  # Mark as flag
                self.flags += 1
                self.update_status()
        elif button["text"] == "🚩":
            button.config(text="", fg="black")  # Unmark
            self.flags -= 1
            self.update_status()

    def lose_game(self, clicked_r: int, clicked_c: int) -> None:
        """Handle game loss scenario

        Args:
            clicked_r: Row index of the mine that was clicked
            clicked_c: Column index of the mine that was clicked
        """
        # Game over, loss
        self.game_over = True
        # Show all mines, mark incorrectly flagged ones
        for r, c in self.mine_locations:
            if (r, c) in self.buttons:  # Check if button exists
                button = self.buttons[(r, c)]
                if r == clicked_r and c == clicked_c:
                    button.config(
                        text="💥",
                        bg="red",
                        state=tk.DISABLED,
                        disabledforeground="black",
                    )  # Clicked mine
                elif button["text"] != "🚩":  # Correctly flagged mines remain flagged
                    button.config(
                        text="💣",
                        bg="lightgrey",
                        state=tk.DISABLED,
                        disabledforeground="black",
                    )  # Other mines
        # Mark incorrectly flagged cells and disable remaining buttons
        for (r, c), button in self.buttons.items():
            if button["text"] == "🚩" and (r, c) not in self.mine_locations:
                button.config(
                    text="❌", state=tk.DISABLED, disabledforeground="red"
                )  # Incorrect flag
            elif (
                button["state"] == tk.NORMAL
            ):  # Disable remaining buttons that are not mines
                button.config(state=tk.DISABLED)
        if self.show_messages:
            messagebox.showerror(
                "Game Over", "Game over! You stepped on a mine."
            )  # Show message after updating UI

    def win_game(self) -> None:
        """Handle game win scenario"""
        # Game win
        self.game_over = True
        # Automatically flag all remaining mines
        for r, c in self.mine_locations:
            if (r, c) in self.buttons and self.buttons[(r, c)][
                "state"
            ] == tk.NORMAL:  # Only flag unrevealed mines
                self.buttons[(r, c)].config(
                    text="🚩", fg="green", state=tk.DISABLED, disabledforeground="green"
                )
        # Disable any remaining normal buttons (shouldn't be any if win condition is met correctly)
        for button in self.buttons.values():
            if button["state"] == tk.NORMAL:
                button.config(state=tk.DISABLED)
        if self.show_messages:
            messagebox.showinfo(
                "Win", "Congratulations! You won!"
            )  # Show message after updating UI

    def update_status(self) -> None:
        """Update the status bar with current game information"""
        # Update status bar label
        remaining_mines = self.mines - self.flags
        self.status_label.config(
            text=f"Total Mines: {self.mines} | Remaining: {remaining_mines}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()
