FROM python:3.10

WORKDIR /bot

#ENV APPLICATION_ID=<Application ID here>
#ENV TOKEN=<Token here>
#ENV LAVALINK_PASSWORD=<Lavalink Password here>
#ENV LAVALINK_HOST=<Lavalink Host here>

RUN pip install discord.py
RUN pip install wavelink
RUN pip install easy-pil

COPY bot.py /bot
COPY botDB.sql /bot
RUN mkdir /bot/cogs
COPY cogs /bot/cogs

CMD ["python", "bot.py"]