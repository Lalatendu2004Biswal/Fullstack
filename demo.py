from flask import Flask,render_template,redirect,url_for

app=Flask(__name__) #here app is an instance of Flask class(variable) that contains the main file of the flask project to run the entire project

@app.route('/')
def home():
   # return "Hello, Flask!"--this will directly show the text on the home page
   # #return redirect(url_for('index')) - this will directly open the index page as the home page

@app.route('/index')
def index():
    return render_template('index.html')

if __name__ == '__main__':#thia condition ensures that the Flask app runs only when this script is executed directly. and it also shows that this is the main entry point of the application.
    app.run(debug=True)