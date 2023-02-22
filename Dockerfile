FROM python:3.9

WORKDIR /app

RUN pip install discord.py
RUN pip install nextcord[voice]
RUN pip install wavelink==1.2.5

COPY . .

CMD ["python", "bot.py"]