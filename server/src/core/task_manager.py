from celery import Celery
from kombu import Queue

app = Celery('tasks',
             broker='pyamqp://guest@localhost//',
             backend='rpc://')

app.conf.task_queues = [
    Queue('high_priority', routing_key='high.#'),
    Queue('default', routing_key='task.#'),
    Queue('low_priority', routing_key='low.#')
]

@app.task(queue='high_priority')
def process_job_offer_task(job_data):
    """Traitement asynchrone d'une offre via Celery"""
    # ... logique de traitement ...