from bot.mera_bot import MeraBot


def main() -> None:
    """
    Entry point of the trading bot.

    Initializes the MeraBot instance and starts its execution loop.
    """
    merabot: MeraBot = MeraBot()
    merabot.run()


if __name__ == "__main__":
    main()
