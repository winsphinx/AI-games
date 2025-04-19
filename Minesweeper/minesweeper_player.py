import tkinter as tk
from minesweeper import Minesweeper  # Import the Minesweeper game class
from minesweeper_utils import OutputLogger, MinePlayer

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    game_window = tk.Toplevel(root)  # Create game window
    # You can also set an initial position for the game window here, e.g., '+100+100'
    game_window.geometry("+100+100")
    game = Minesweeper(
        game_window, rows=10, cols=10, mines=10
    )  # Game instance uses the new window
    game.show_messages = False  # Disable message boxes when running through player

    logger = OutputLogger(root)  # Create logger instance
    player = MinePlayer(game, logger)  # Pass the logger to the player
    game.on_restart_callback = player.restart_auto_play  # Set callback

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
            pass  # Window may have been destroyed
        try:
            game_window.destroy()
        except tk.TclError:
            pass  # Window may have been destroyed
        # root.quit() might be another option for root.destroy(), if mainloop needs to exit cleanly first
        # Using destroy() is usually more thorough.
        try:
            root.destroy()  # Destroy the main hidden window, effectively ending the application
        except tk.TclError:
            pass  # Window may have been destroyed

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
        on_closing()  # Call the same cleanup logic
