FROM python:3.10

WORKDIR /bot

COPY bot.py /bot
COPY botDB.sql /bot
RUN mkdir /bot/cogs
COPY cogs /bot/cogs
COPY requirements.txt /bot

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]