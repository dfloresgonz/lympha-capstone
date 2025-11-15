import json
import mlflow
import os
import pandas as pd
import numpy as np

user = "grupo5"
model_name = f"model-attrition-{user}"
model_version = "latest"
model_uri = f"models:/{model_name}/{model_version}"


def lambda_handler(event, context):
  try:
    os.environ['MLFLOW_TRACKING_USERNAME'] = 'name'
    os.environ['MLFLOW_TRACKING_PASSWORD'] = 'pass'

    tracking_uri = os.environ['MLFLOW_TRACKING_SERVER_ARN']
    print(f"Tracking URI: {tracking_uri}")

    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow tracking URI set to: {tracking_uri}")

    model = mlflow.xgboost.load_model(model_uri)

    input_data = json.loads(event['body']).get('input_data', {})
    print(f"Received input data: {input_data}")

    data = pd.DataFrame({
        'flg_bancarizado': [input_data.get('flg_bancarizado', 1)],
        'edad': [input_data.get('edad', 35.0)],
        'antiguedad': [input_data.get('antiguedad', 5.0)],
        'sdo_activo_menos0': [input_data.get('sdo_activo_menos0', 0)],
        'sdo_activo_menos1': [input_data.get('sdo_activo_menos1', 0)],
        'sdo_activo_menos2': [input_data.get('sdo_activo_menos2', 0)],
        'flg_seguro_menos0': [input_data.get('flg_seguro_menos0', 0)],
        'flg_seguro_menos1': [input_data.get('flg_seguro_menos1', 0)],
        'flg_seguro_menos2': [input_data.get('flg_seguro_menos2', 0)],
        'flg_nomina': [input_data.get('flg_nomina', 0)],
        'nro_acces_canal1_menos0': [input_data.get('nro_acces_canal1_menos0', 0)],
        'nro_acces_canal2_menos0': [input_data.get('nro_acces_canal2_menos0', 0)],
        'nro_acces_canal3_menos0': [input_data.get('nro_acces_canal3_menos0', 0)],

        'flag_lima_provincia_encoded': [input_data.get('flag_lima_provincia_encoded', 0)],
        'rang_ingreso_encoded': [input_data.get('rang_ingreso_encoded', 0)],
        'rang_sdo_pasivo_menos0_encoded': [input_data.get('rang_sdo_pasivo_menos0_encoded', 0)]
    })

    pred = model.predict_proba(data)[:, 1][0]
    pred = float(pred)

    all_probs = model.predict_proba(data)[0]
    prob_no_churn = float(all_probs[0])
    prob_churn = float(all_probs[1])

    binary_pred = int(model.predict(data)[0])

    print(f"pred: {pred}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Éxito',
            'churn_probability': pred,
            'no_churn_probability': prob_no_churn,
            'binary_prediction': binary_pred,
            'prediction_label': 'CHURN' if binary_pred == 1 else 'NO_CHURN'
        })
    }
  except Exception as e:
    print(f"Error in lambda_handler: {e}")

    return {
        'statusCode': 500,
        'body': json.dumps({'message': 'Error', 'error': str(e)})
    }
