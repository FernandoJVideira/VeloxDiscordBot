FROM python:3.10

WORKDIR /bot

RUN pip install discord.py
RUN pip install wavelink
RUN pip install easy-pil

COPY bot.py /bot
COPY botDB.sql /bot
RUN mkdir /bot/cogs
COPY cogs /bot/cogs

CMD ["python", "bot.py"]