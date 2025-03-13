from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import os
import pickle

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'MiniProject'
app.config['MYSQL_CHARSET'] = 'utf8' 
# Initialize MySQL connection
mysql = mysql.connector.connect( 
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB'],
    charset=app.config['MYSQL_CHARSET']
)


file_path = r"best_model.pkl"
#print(file_path)
# Load the model from the Pickle file
with open("best_model.pkl", 'rb') as f:
    model = pickle.load(f)          #randomforest model as it got highest accuracy
    
filepath = r"tabnet_model.pkl"
with open("tabnet_model.pkl",'rb') as f1:
   Nephropathy_model = pickle.load(f1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    # Basic validation (consider using Flask-WTF for more robust validation)
    if not email or not password:
      return "Email and password are required!", 400  # Bad request

    cursor = mysql.cursor()
    try:
      cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
      mysql.commit()
      return redirect(url_for('login'))
    except mysql.connector.Error as err:
      # Handle database errors gracefully (log the error, display user-friendly message)
      app.logger.error(f"Database error: {err}")
      return "An error occurred during registration. Please try again later.", 500

  return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = None  # Initialize the user variable
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.cursor(dictionary=True) 
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            return jsonify({'success': True, 'redirect': url_for('home')})
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password!'})

    return render_template('login.html')

@app.route('/home',methods=['GET','POST'])
def home():
   return render_template('home.html') 
      

@app.route('/diabetes_form', methods=['GET', 'POST'])
def diabetes_form():
    if request.method == 'POST':
        form_data = {
            'age': request.form['age'],
            'gender': request.form['gender'].lower(),  # Normalize gender to lowercase
            'polyuria': request.form['polyuria'],
            'polydipsia': request.form['polydipsia'],
            'sudden_weight_loss': request.form['sudden_weight_loss'],
            'weakness': request.form['weakness'],
            'polyphagia': request.form['polyphagia'],
            'genital_thrush': request.form['genital_thrush'],
            'visual_blurring': request.form['visual_blurring'],
            'itching': request.form['itching'],
            'irritability': request.form['irritability'],
            'delayed_healing': request.form['delayed_healing'],
            'partial_paresis': request.form['partial_paresis'],
            'muscle_stiffness': request.form['muscle_stiffness'],
            'alopecia': request.form['alopecia'],
            'obesity': request.form['obesity']
        }
        
        # Convert to DataFrame
        df = pd.DataFrame([form_data])
        
        # Log the input data for debugging
        app.logger.debug(f"Input data: {df}")
        
        # Make prediction using the model
        prediction = model.predict_proba(df)
        # Preprocess the data
        # data = np.array([[age, gender, polyuria, polydipsia, sudden_weight_loss, weakness,polyphagia, genital_thrush, visual_blurring, itching, irritability, delayed_healing, partial_paresis, muscle_stiffness, alopecia, obesity]])  # Adjust as needed for other symptoms
        #  # Log the input data for debugging
        # app.logger.debug(f"Input data: {data}")
        # # Make prediction using the model
        # prediction = model.predict(data)
        # Process prediction result (you may need to post-process depending on your model output)
        pred = prediction[0][1]
        pred_percentage = round(pred * 100, 2)
        consult_doctor = pred_percentage > 75

        return render_template('PredictionResult.html', prediction=pred_percentage, consult_doctor=consult_doctor)
    

    return render_template('diabetes_form.html')


@app.route('/Nephropathy_Form', methods=['GET', 'POST'])
def Nephropathy_Form():
    if request.method == 'POST':
        form_dataN = {
            'age': int(request.form['age']),
            'Diabetes duration (y)': int(request.form['diabetes_duration']),
            'Height(cm)': float(request.form['height']),
            'Weight(kg)': float(request.form['weight']),
            'BMI (kg/m2)': float(request.form['bmi']),
            'SBP (mmHg)': float(request.form['sbp']),
            'DBP (mmHg)': float(request.form['dbp']),
            'HbA1c (%)': float(request.form['hba1c']),
            'FBG (mmol/L)': float(request.form['fbg']),
            'TG（mmoll）': float(request.form['tg']),
            'C-peptide (ng/ml）': float(request.form['c_peptide']),
            'TC（mmoll）': float(request.form['tc']),
            'HDLC（mmoll）': float(request.form['hdlc']),
            'LDLC（mmoll）': float(request.form['ldlc']),
            'Diabetic retinopathy (DR)': int(request.form['retinopathy']),
            'Insulin': int(request.form['insulin']),
            'Metformin': int(request.form['metformin']),
            'Lipid lowering drugs': int(request.form['lipid_lowering_drugs'])
        }
        
        # Convert to DataFrame
        df1 = pd.DataFrame([form_dataN])
        
        # Log the input data for debugging
        app.logger.debug(f"Input data: {df1}")
        
        # Make prediction using the model
        prediction = Nephropathy_model.predict_proba(df1.to_numpy())
        
        pred = prediction[0][1]
        pred_percentage = round(pred * 100, 2)
        # Define risk level
        if pred_percentage <= 50:
            risk_level = "low"
        elif 50 < pred_percentage <= 75:
            risk_level = "moderate"
        else:
            risk_level = "high"

        return render_template('predictionResultNephropathy.html', prediction=pred_percentage, risk_level=risk_level)
    
    return render_template('Nephropathy_Form.html')

if __name__ == '__main__':
    app.run(debug=True)
