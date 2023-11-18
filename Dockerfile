FROM python:3.10

WORKDIR /bot

#ENV TOKEN=<Token here>
#ENV TWITCH_CLIENT_ID=<Client ID here>
#ENV TWITCH_CLIENT_SECRET=<Client Secret here>
#ENV TWITCH_AUTH_TOKEN=<Auth Token here>
#ENV LAVALINK_PASSWORD='<Lavalink Password here>'

RUN pip install discord.py
RUN pip install wavelink
RUN pip install easy-pil
RUN pip install twitchAPI

COPY bot.py /bot
COPY botDB.sql /bot
RUN mkdir /bot/cogs
COPY cogs /bot/cogs

CMD ["python", "bot.py"]