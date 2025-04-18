import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import random
from minesweeper import Minesweeper # Import the Minesweeper game class

class OutputLogger:
    def __init__(self, master):
        self.log_window = tk.Toplevel(master)
        self.log_window.title("Auto Minesweeper Log")
        # Set log window size and initial position (e.g., width 400, height 500, offset 500 pixels from left, 100 pixels from top)
        # You can adjust the '+500+100' values as needed
        self.log_window.geometry("400x500+500+100")
        self.log_text = scrolledtext.ScrolledText(self.log_window, wrap=tk.WORD, state='disabled')
        self.log_text.pack(expand=True, fill='both')

    def log(self, message):
        """Log the message to the log window"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Scroll to the bottom
        self.log_text.config(state='disabled')
        self.log_window.update_idletasks() # Ensure the interface is updated

class MinePlayer:
    def __init__(self, game_instance, logger):
        self.game = game_instance
        self.logger = logger # Use the passed logger
        self.rows = game_instance.rows
        self.cols = game_instance.cols
        self.board_state = {} # Used to store our knowledge of the board: 'H'idden, 'R'evealed, 'F'lagged
        self.initialize_board_state()
        self.play_delay = 50 # ms between steps
        self.after_id = None # To store the id of the pending 'after' job
    def initialize_board_state(self):
        """Initialize board state, mark all cells as hidden"""
        for r in range(self.rows):
            for c in range(self.cols):
                self.board_state[(r, c)] = 'H' # H for Hidden

    def update_board_state(self):
        """Update board state based on the game interface"""
        for r in range(self.rows):
            for c in range(self.cols):
                button = self.game.buttons[(r, c)]
                button_text = button['text']
                button_state = button['state']

                if button_state == tk.DISABLED and button_text != '🚩':
                    self.board_state[(r, c)] = 'R' # R for Revealed
                elif button_text == '🚩':
                    self.board_state[(r, c)] = 'F' # F for Flagged
                elif button_state == tk.NORMAL and button_text == '':
                    self.board_state[(r, c)] = 'H' # H for Hidden
                # Other cases not handled specially for now

    def get_neighbors(self, r, c):
        """Get neighbor cell coordinates"""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def make_move(self):
        """Decide and execute the next action based on the current board state"""
        self.update_board_state() # Update state before each move

        made_move = self.flag_sure_mines()
        if made_move:
            return True

        made_move = self.click_sure_safe_cells()
        if made_move:
            return True

        return False # No more deterministic moves available


    def flag_sure_mines(self):
        """
        Find a revealed number cell N, if there are N unrevealed cells around it (including flagged ones),
        then flag all unrevealed and unflagged neighbors as mines.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board_state[(r, c)] == 'R':
                    button = self.game.buttons[(r, c)]
                    try:
                        adjacent_mines_count = int(button['text'])
                        if adjacent_mines_count > 0:
                            neighbors = self.get_neighbors(r, c)
                            hidden_neighbors = [n for n in neighbors if self.board_state[n] in ['H', 'F']]
                            unflagged_hidden_neighbors = [n for n in hidden_neighbors if self.board_state[n] == 'H']

                            if len(hidden_neighbors) == adjacent_mines_count and len(unflagged_hidden_neighbors) > 0:
                                for nr, nc in unflagged_hidden_neighbors:
                                    self.logger.log(f"Strategy 1: Flagging mine at ({nr}, {nc}) based on ({r}, {c})={adjacent_mines_count}")
                                    self.game.on_right_click(nr, nc) # Simulate right-click to flag
                                    self.board_state[(nr, nc)] = 'F' # Update internal state
                                return True # Flagging action performed
                    except (ValueError, TypeError):
                        continue
        return False


    def click_sure_safe_cells(self):
        """
        Find a revealed number cell N, if there are already N flagged cells around it,
        then click all other unrevealed and unflagged neighbors.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                 if self.board_state[(r, c)] == 'R':
                    button = self.game.buttons[(r, c)]
                    try:
                        adjacent_mines_count = int(button['text'])
                        if adjacent_mines_count > 0:
                            neighbors = self.get_neighbors(r, c)
                            flagged_neighbors = [n for n in neighbors if self.board_state[n] == 'F']
                            hidden_unflagged_neighbors = [n for n in neighbors if self.board_state[n] == 'H']

                            if len(flagged_neighbors) == adjacent_mines_count and len(hidden_unflagged_neighbors) > 0:
                                for nr, nc in hidden_unflagged_neighbors:
                                    self.logger.log(f"Strategy 2: Clicking safe cell ({nr}, {nc}) based on ({r}, {c})={adjacent_mines_count}")
                                    self.game.on_click(nr, nc) # Simulate left-click
                                return True # Clicking action performed
                    except (ValueError, TypeError):
                        continue
        return False

    def make_random_guess(self):
        """Randomly select an unrevealed and unflagged cell to click"""
        hidden_cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board_state[(r, c)] == 'H':
                    hidden_cells.append((r, c))

        if hidden_cells:
            r, c = random.choice(hidden_cells)
            self.logger.log(f"Strategy 3: Random guess click at ({r}, {c})")
            self.game.on_click(r, c) # Simulate left-click
            return True
        return False

    def start_initial_play(self):
        """Start the auto game, perform the first click and start the loop"""
        self.logger.log("Starting a new round of auto play...")
        # Make sure the board state is fresh, especially after a restart
        self.initialize_board_state()
        self.update_board_state() # Get initial state if game restarted mid-play

        # Cancel any previous loop first
        if self.after_id:
            self.game.master.after_cancel(self.after_id)
            self.after_id = None

        # Check if game is already over (e.g., instant loss on first click simulation)
        if self.game.game_over:
             self.logger.log("The game ended at the start.")
             return

        # Make the first move randomly
        hidden_cells = [pos for pos, state in self.board_state.items() if state == 'H']
        if not hidden_cells:
            self.logger.log("No hidden cells to start with.")
            return

        start_r, start_c = random.choice(hidden_cells)
        # start_r, start_c = random.choice([(0,0), (0, self.cols-1), (self.rows-1, 0), (self.rows-1, self.cols-1)]) # Alternative: corners
        self.logger.log(f"Initial click: ({start_r}, {start_c})")
        self.game.on_click(start_r, start_c)
        self.game.master.update() # Update UI immediately

        # Start the step-by-step loop
        self.after_id = self.game.master.after(self.play_delay, self.auto_play_step)

    def auto_play_step(self):
        """Execute one step of auto minesweeper logic and schedule the next step"""
        if self.game.game_over:
            self.logger.log("Game over, restarting game automatically.")
            self.after_id = None
            self.game.restart_game()
            self.initialize_board_state()
            self.game.master.after(200, self.start_initial_play)
            return

        made_move = self.make_move() # Try deterministic moves

        if not made_move:
            # No deterministic move found, try random guess
            if not self.make_random_guess():
                # No deterministic move and no cell to guess, game might be won or stuck
                # Check win condition (though game.game_over should ideally cover this)
                self.update_board_state() # Ensure state is current
                hidden_cells = [pos for pos, state in self.board_state.items() if state == 'H']
                flagged_cells = [pos for pos, state in self.board_state.items() if state == 'F']
                if len(hidden_cells) == 0 and len(flagged_cells) == self.game.mines:
                     self.logger.log("All non-mine cells are revealed, or all mines are flagged.")
                else:
                     self.logger.log("No deterministic moves, and no cells to guess.")
                self.after_id = None
                return # Stop the loop

        self.game.master.update() # Update UI after move

        # Schedule the next step
        self.after_id = self.game.master.after(self.play_delay, self.auto_play_step)

    def restart_auto_play(self):
        """Respond to game restart event"""
        self.logger.log("Received restart signal, re-initializing auto player...")
        # Cancel any pending auto_play_step from the previous game
        if self.after_id:
            self.game.master.after_cancel(self.after_id)
            self.after_id = None
        # Reset internal state (game object itself is reset by its own restart)
        self.initialize_board_state()
        # Schedule the start of the new game after a short delay
        # This delay allows the game board UI to fully reset
        self.game.master.after(200, self.start_initial_play)
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Hide the main Tkinter window

    game_window = tk.Toplevel(root) # Create game window
    # You can also set an initial position for the game window here, e.g., '+100+100'
    game_window.geometry("+100+100")
    game = Minesweeper(game_window, rows=10, cols=10, mines=10) # Game instance uses the new window
    game.show_messages = False # Disable message boxes when running through player

    logger = OutputLogger(root) # Create logger instance
    player = MinePlayer(game, logger) # Pass the logger to the player
    game.on_restart_callback = player.restart_auto_play # Set callback

    def on_closing():
        """Handle window close event."""
        if player.after_id:
            try:
                # Cancel using the window associated with the 'after' task
                # In this context, player.game.master is game_window
                game_window.after_cancel(player.after_id)
            except tk.TclError:
                 # Handle the case where the window may have been destroyed
                pass
            player.after_id = None

        # Gracefully destroy the window
        try:
            logger.log_window.destroy()
        except tk.TclError:
            pass # Window may have been destroyed
        try:
            game_window.destroy()
        except tk.TclError:
            pass # Window may have been destroyed
        # root.quit() might be another option for root.destroy(), if mainloop needs to exit cleanly first
        # Using destroy() is usually more thorough.
        try:
            root.destroy() # Destroy the main hidden window, effectively ending the application
        except tk.TclError:
            pass # Window may have been destroyed


    # Register close handler for game window
    game_window.protocol("WM_DELETE_WINDOW", on_closing)
    # Optional: also register for log window if it should close independently
    # logger.log_window.protocol("WM_DELETE_WINDOW", on_closing)
    # It might be better to close all content when closing the game window.

    # Use after to start the initial game loop
    root.after(500, player.start_initial_play)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing() # Call the same cleanup logic