from airflow.decorators import task, dag
from airflow.providers.docker.operators.docker import DockerOperator

from datetime import datetime, timedelta

default_args = { 
    'retries': 3,
    'retry_delay': timedelta(minutes=60)
    }

@dag(
    start_date=datetime(2024, 8, 26), 
    schedule_interval='0 7 * * *', 
    catchup=False,
    default_args=default_args,
    tags=['joao'])

def trade_advisor_dag():
    trade_advisor = DockerOperator(
        task_id='trade_advisor',
        image='trade-advisor',
        entrypoint='python',
        docker_url='unix://var/run/docker.sock',
        network_mode='bridge',
        environment = {
            "TWILIO_ACCOUNT_SID": '{{var.value.twilio_account_sid}}',
            "TWILIO_AUTH_TOKEN": '{{var.value.twilio_auth_token}}',
            "WHATSAPP_SENDER_NUMBER": '{{var.value.trade_advisor_whatsapp_sender_number}}',
            "WHATSAPP_RECEIVER_NUMBER": '{{var.value.trade_advisor_whatsapp_receiver_number}}',
            "SENDGRID_API_KEY": '{{var.value.sendgrid_api_key}}',
            "EMAIL_SENDER": '{{var.value.trade_advisor_email_sender}}',
            "EMAIL_RECEIVER": '{{var.value.trade_advisor_email_receiver}}'
        },
        command="/app/src/cli/cli.py trade-today --output=email,whatsapp --tickers AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM -p 2024-07-18,META,2.09692,476.89 -p 2024-07-18,GOOG,5.56917,179.56 -p 2024-07-18,NVDA,8.28706,120.67 -p 2024-07-18,AMZN,2.68962,185.90 -p 2024-07-18,MSFT,0.5328,438.16"
    )
        
    trade_advisor
    
dag = trade_advisor_dag()

