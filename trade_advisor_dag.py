from airflow.decorators import task, dag
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable
from datetime import datetime, timedelta

default_args = { 
    'retries': 3,
    'retry_delay': timedelta(minutes=10)
    }

def get_user_list():
    # trade_advisor_user_list: ["alice", "bob", "carol"]
    return Variable.get("trade_advisor_user_list", default_var=[], deserialize_json=True)

@dag(
    start_date=datetime(2024, 8, 26), 
    schedule_interval='0 4 * * 1-6', # [Mon..Sat] at 4AM (UTC) 
    catchup=False,
    default_args=default_args,
    tags=['joao'])

def trade_advisor_dag():

    trade_advisor_yfinance_download = DockerOperator(
        task_id=f'trade_advisor_yfinance_download',
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
            "EMAIL_RECEIVER": '{{var.value.trade_advisor_email_receiver}}',
            "AWS_ACCESS_KEY_ID": '{{var.value.trade_advisor_aws_access_key_id}}',
            "AWS_SECRET_ACCESS_KEY": '{{var.value.trade_advisor_aws_secret_access_key}}',
            "TRADE_ADVISOR_S3_BUCKET": '{{var.value.trade_advisor_s3_bucket}}',
            "OPEN_EXCHANGE_APP_ID": '{{var.value.trade_advisor_open_exchange_app_id}}',
            "TWELVEDATA_API_KEY": '{{var.value.trade_advisor_twelvedata_api_key}}'
        },
        command=f"/app/src/cli/cli.py download-yfinance-data"
    )


    for user in get_user_list():
        trade_advisor = DockerOperator(
            task_id=f'trade_advisor_{user}',
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
                "EMAIL_RECEIVER": '{{var.value.trade_advisor_email_receiver}}',
                "AWS_ACCESS_KEY_ID": '{{var.value.trade_advisor_aws_access_key_id}}',
                "AWS_SECRET_ACCESS_KEY": '{{var.value.trade_advisor_aws_secret_access_key}}',
                "TRADE_ADVISOR_S3_BUCKET": '{{var.value.trade_advisor_s3_bucket}}',
                "OPEN_EXCHANGE_APP_ID": '{{var.value.trade_advisor_open_exchange_app_id}}',
                "TWELVEDATA_API_KEY": '{{var.value.trade_advisor_twelvedata_api_key}}'
            },
            command=f"/app/src/cli/cli.py trade-today --user={user} --output=email --rapid"
        )
            
        trade_advisor_yfinance_download >> trade_advisor
    
dag = trade_advisor_dag()