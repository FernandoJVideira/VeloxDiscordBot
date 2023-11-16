FROM python:3.10

WORKDIR /bot

ENV APPLICATION_ID='1169299903378378772'
ENV TOKEN='MTE2OTI5OTkwMzM3ODM3ODc3Mg.GyY4FY.OR98Rvvma_r1UOhziRqnMjy7C5-M7EjSN6ULBw'
ENV TWITCH_CLIENT_ID='e6m1lfmynhnzghl1vdzep2wwvd5z77'
ENV TWITCH_CLIENT_SECRET='4b8qzdr0ahcguntn8vkyjaocn0dp72'
ENV TWITCH_AUTH_TOKEN='rrnv4v9pgyw0m6np1ynz01yivdlj5f'
ENV LAVALINK_PASSWORD='zGqx4tXszM3'

RUN pip install discord.py
RUN pip install wavelink
RUN pip install easy-pil
RUN pip install twitchAPI

COPY bot.py /bot
RUN mkdir /bot/cogs
COPY cogs /bot/cogs

CMD ["python", "bot.py"]