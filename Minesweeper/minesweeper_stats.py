import tkinter as tk
import matplotlib.pyplot as plt
from minesweeper import Minesweeper  # Import the Minesweeper game class
from minesweeper_utils import OutputLogger, MinePlayer


class MineStatsRunner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game_window = tk.Toplevel(self.root)
        self.game_window.geometry("+100+100")

        self.stats = {
            mines: {"wins": 0, "losses": 0} for mines in range(1, 101)
        }  # Test 1-100 mines
        self.total_games = 0
        self.runs_per_mines = 10  # Run each mine count ten times
        self.current_mines = 1
        self.current_run = 0

        self.game = Minesweeper(self.game_window, rows=10, cols=10, mines=1)
        self.game.show_messages = False
        self.game.restart_button.config(state=tk.DISABLED)  # Disable the restart button
        self.logger = OutputLogger(self.root)
        self.player = MinePlayer(self.game, self.logger)
        self.game.on_restart_callback = self.player.restart_auto_play

    def run_single_test(self):
        """Run a single test iteration for current mine count"""
        self.game.mines = self.current_mines
        self.game.restart_game()
        self.player.start_initial_play()
        # Start checking result after game starts
        self.root.after(100, self.check_result)

    def check_result(self):
        """Check game result and proceed to next test"""
        if not self.game.game_over:
            # Game still running, check again later
            self.root.after(100, self.check_result)
            return

        # Record game result
        if (
            self.game.cells_revealed
            == self.game.rows * self.game.cols - self.game.mines
        ):
            self.stats[self.current_mines]["wins"] += 1
        else:
            self.stats[self.current_mines]["losses"] += 1

        self.total_games += 1
        self.current_run += 1
        progress = (
            self.total_games / (100 * self.runs_per_mines)
        ) * 100  # Testing 1-100 mines, each multiple times
        self.logger.log(
            f"Progress: {progress:.1f}% | Mines: {self.current_mines} | Run: {self.current_run}/{self.runs_per_mines}"
        )

        # Check if more runs are needed for the current mine count
        if self.current_run < self.runs_per_mines:
            self.root.after(100, self.run_single_test)
        else:
            # Move to next mine count
            if self.current_mines < 100:
                self.current_mines += 1
                self.current_run = 0
                self.root.after(100, self.run_single_test)
            else:
                # All tests completed
                self.print_final_stats()

    def plot_histogram(self):
        """Plot win rate histogram with enhanced styling and save to file"""
        mines_counts = []
        win_rates = []

        for mines_count in range(1, 101):
            total = self.stats[mines_count]["wins"] + self.stats[mines_count]["losses"]
            win_rate = self.stats[mines_count]["wins"] / total * 100 if total > 0 else 0
            mines_counts.append(mines_count)
            win_rates.append(win_rate)

        plt.figure(figsize=(12, 7))
        plt.rcParams["font.sans-serif"] = [
            "DejaVu Sans"
        ]  # Use default font to avoid warnings
        plt.rcParams["axes.unicode_minus"] = False  # Fix minus sign display issue
        plt.bar(mines_counts, win_rates, color="skyblue", edgecolor="black")
        plt.xlabel("Number of Mines", fontsize=12)
        plt.ylabel("Win Rate (%)", fontsize=12)
        plt.title("Minesweeper Win Rate by Mine Count", fontsize=14, pad=15)
        # Show only multiples of 5 on x-axis
        plt.xticks(range(0, 101, 5), fontsize=10)
        plt.yticks(fontsize=10)
        plt.ylim(0, 100)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        plt.savefig(
            os.path.join(current_dir, "win_rate_histogram.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def print_final_stats(self):
        """Print final statistics to log window and plot histogram"""
        stats_text = "\nFinal Statistics:\n"
        stats_text += "Mines | Win Rate\n"
        stats_text += "------|---------\n"

        for mines_count in range(1, 101):
            total = self.stats[mines_count]["wins"] + self.stats[mines_count]["losses"]
            win_rate = self.stats[mines_count]["wins"] / total * 100 if total > 0 else 0
            stats_text += f"{mines_count:5} | {win_rate:.1f}%\n"

        # Output to log window
        self.logger.log(stats_text)

        # Plot histogram
        self.plot_histogram()
        self.logger.log("\nWin rate histogram saved to 'win_rate_histogram.png'")

    def start(self):
        """Start the test sequence"""
        self.run_single_test()
        self.root.mainloop()

    def on_closing(self):
        """Handle window close event."""
        # Cancel any pending callbacks
        if hasattr(self, "player") and self.player.after_id:
            try:
                self.game_window.after_cancel(self.player.after_id)
            except tk.TclError:
                pass

        # Destroy windows in reverse order of creation
        try:
            if hasattr(self, "logger") and hasattr(self.logger, "log_window"):
                self.logger.log_window.destroy()
        except tk.TclError:
            pass

        try:
            if hasattr(self, "game_window"):
                self.game_window.destroy()
        except tk.TclError:
            pass

        try:
            if hasattr(self, "root"):
                self.root.destroy()
        except tk.TclError:
            pass

        # Force exit if needed
        import os

        os._exit(0)


if __name__ == "__main__":
    tester = MineStatsRunner()
    tester.game_window.protocol("WM_DELETE_WINDOW", tester.on_closing)
    try:
        tester.start()
    except KeyboardInterrupt:
        tester.on_closing()
