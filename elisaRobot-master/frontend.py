# from dearpygui.core import *
# from dearpygui.simple import *
import dearpygui.dearpygui as d
from platform import python_version
from tg_bot.__main__ import STATS

try:
    from telegram import __version__ as pver
except ImportError:
    pver = "N/A"

# with d.window("About"):
with d.window():
    d.add_text("Ōɖìղ • オーディン telegram bot")
    d.add_text("Maintained with <3 by ルーク(github.com/itsLuuke)")
    d.add_text("Enviroment:")
    d.add_text(f"Bot lib: python-telegram-bot v{pver}.", bullet=True)
    d.add_text(f"Python version: {python_version()}.", bullet=True)
    d.add_text("Source:")
    d.add_text("GitHub: github.com/itsLuuke", bullet=True)
    d.add_text("\n*Bot statistics*:\n"+ "\n".join([mod.__stats__() for mod in STATS]))

# with d.window("stats"):



# d.start_dearpygui()
d.start_dearpygui(primary_window="About")
