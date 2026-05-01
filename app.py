from flask import Flask,request,render_template,url_for,session,flash,redirect
from otp import genotp
import bcrypt
import os
from cmail import send_mail
from stoken import endata,dedata
from mysql.connector import (connection)
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import mysql.connector


mydb = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=44445
)
app=Flask(__name__)
app.secret_key=b'a6*\xf9\xf6'
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/admincreate',methods=['GET','POST'])
def admincreate():
    if request.method=='POST':
        print(request.form)
        adminname=request.form['username']
        adminemail=request.form['email']
        adminpassword=request.form['password']
        adminaddress=request.form['address']
        adminagree=request.form['agree']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(email) from admindata where email=%s',[adminemail])
            count_email=cursor.fetchone() #(1,) or (0,)
        except Exception as e:
            print(e)
            flash('Database connection lost')
            return redirect(url_for('admincreate'))
        else:
            if count_email[0]== 0:
                gotp=genotp()
                admindata={'adminname':adminname,'adminemail':adminemail,'adminpassword':adminpassword,'adminaddress':adminaddress,'adminagree':adminagree,'adminotp':gotp}
                
                subject='Use otp for Ecommee App verification'
                body=f'otp for Admin registration : {gotp}'
                send_mail(to=adminemail,subject=subject,body=body)
                flash(f'OTP has sent to given email{adminemail}')
                return redirect(url_for('adminotpverify',enadmin=endata(data=admindata)))
            elif count_email[0]==1:
                flash('Email already existed')
                return redirect(url_for('adminlogin'))
    return render_template('admincreate.html')
@app.route('/adminotpverify/<enadmin>',methods=['GET','POST'])
def adminotpverify(enadmin):
    try:
        deadmin=dedata(enadmin) #{'adminname':'anusha','adminemail':adminemail,'adminpassword':adminpassword,'adminaddress':adminaddress,'adminagree':adminagree,'adminotp':gotp}
    except SignatureExpired as e:
        print(f"Token has expired. Reason: {e}")
        flash('otp has expired.')
        return redirect(url_for('admincreate'))
    except Exception as e:
        print(e)
        flash('couldnt verify otp')
        return redirect(url_for('admincreate'))
    
    else:
        if request.method=='POST':
            given_otp=request.form['otp']
            if given_otp==deadmin['adminotp']:
                try:
                    hash_pwd=bcrypt.hashpw(deadmin['adminpassword'].encode('utf-8'),bcrypt.gensalt())
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('insert into admindata(username,email,password,agreed,address) values(%s,%s,%s,%s,%s)',[deadmin['adminname'],deadmin['adminemail'],hash_pwd,deadmin['adminagree'],deadmin['adminaddress']])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('could not store your details')
                    return redirect(url_for('admincreate'))
                else:
                    flash('details stored successfully')
                    return redirect(url_for('adminlogin'))
            else:
                flash('wrong otp')
                
    return render_template('adminotp.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=='POST':
        login_email=request.form['email']
        login_password=request.form['password'].encode('utf-8')
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(email) from admindata where email=%s',[login_email])
            count_email=cursor.fetchone() #(1,) or (0,)
        except Exception as e:
            print(e)
            flash('Database connection lost while login')
            return redirect(url_for('adminlogin'))
        else:
            if count_email[0]==1:
                cursor.execute('select password from admindata where email=%s',[login_email])
                stored_password=cursor.fetchone()
                if bcrypt.checkpw(login_password,stored_password[0]):
                    session['admin']=login_email
                    return redirect(url_for('adminpanel'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('adminlogin'))
            elif count_email[0]==0:
                flash('Email not fount')
                return redirect(url_for('adminlogin'))
    return render_template('adminlogin.html')
@app.route('/adminpanel')
def adminpanel():
    if session.get('admin'):
        return render_template('adminpanel.html')
    else:
        flash('pls login to access dashboard')
        return redirect(url_for('adminlogin'))
@app.route('/additem',methods=['GET','POST'])
def additem():
    if session.get('admin'):
        if request.method=='POST':
            item_name=request.form['title']
            item_description=request.form['Description']
            item_price=request.form['price']
            item_quantity=request.form['quantity']
            item_category=request.form['category']
            item_imagedata=request.files['file']
            imagename=item_imagedata.filename
            print(imagename.split('.'))
            img_name=genotp()+'.'+imagename.split('.')[-1]
            print(img_name)
            filepath=os.path.abspath(__file__)
            print(filepath)
            dpath=os.path.dirname(filepath)
            print(dpath)
            static_path=os.path.join(dpath,'static')
            print(static_path)
            item_imagedata.save(os.path.join(static_path,img_name))
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select adminid from admindata where email=%s',[session.get('admin')])
                admin_id = cursor.fetchone()
                if admin_id:
                    cursor.execute('insert into items(itemid,item_name,item_description,price,quantity,category,item_image,added_by) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s)',[item_name,item_description,item_price,item_quantity,item_category,img_name,admin_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('admindetails not found')
                    return redirect(url_for('additem'))
            except Exception as e:
                print(f'Error is {e}')
                flash('couldnot store item details')
                return redirect(url_for('additem'))
            else:
                flash('Item details added successfully')
                return redirect(url_for('additem'))

        return render_template('additem.html')
    else:
        flash('to add item pls login')
        return redirect(url_for('adminlogin'))
@app.route('/view_allitems')
def view_allitems():
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select adminid from admindata where email=%s',[session.get('admin')])
            admin_id = cursor.fetchone()
            if admin_id:
                cursor.execute('select bin_to_uuid(itemid),item_name,item_description,price,quantity,category,item_image from items where added_by=%s',[admin_id[0]])
                all_itemsdata=cursor.fetchall()
                print(all_itemsdata)
            else:
                flash('admindetails not found')
                return redirect(url_for('additem'))
        except Exception as e:
            print(f'Error is {e}')
            flash('could fetch items data')
            return redirect(url_for('adminpanel'))
        else:
            return render_template('viewall_items.html',all_itemsdata=all_itemsdata)
    else: 
        flash(f'To view all items pls login')
        return redirect(url_for('adminlogin'))
@app.route('/view_item/<itemid>')
def view_item(itemid):
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select adminid from admindata where email=%s',[session.get('admin')])
            admin_id = cursor.fetchone()
            if admin_id:
                cursor.execute('select bin_to_uuid(itemid),item_name,item_description,price,quantity,category,item_image from items where itemid=uuid_to_bin(%s) and added_by=%s',[itemid,admin_id[0]])
                item_data=cursor.fetchone()
                print(item_data)
            else:
                flash('admindetails not found')
                return redirect(url_for('adminpanel'))
        except Exception as e:
            print(f'Error is {e}')
            flash('could fetch items data')
            return redirect(url_for('adminpanel'))
        else:
            return render_template('view_item.html',item_data=item_data)
    else: 
        flash(f'To view all item pls login')
        return redirect(url_for('adminlogin'))
@app.route('/delete_item/<itemid>')
def delete_item(itemid):
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select adminid from admindata where email=%s',[session.get('admin')])
            admin_id = cursor.fetchone()
            if admin_id:
                cursor.execute('select item_image from items where itemid=uuid_to_bin(%s) and added_by=%s',[itemid,admin_id[0]])
                stored_imagename=cursor.fetchone()
                if stored_imagename:
                    filepath=os.path.abspath(__file__)
                    print(filepath)
                    dpath=os.path.dirname(filepath)
                    print(dpath)
                    static_path=os.path.join(dpath,'static')
                    print(static_path)

                    os.remove(os.path.join(static_path,stored_imagename[0]))
                    cursor.execute('delete from items where itemid=uuid_to_bin(%s) and added_by=%s',[itemid,admin_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('Could not find image ')
                    return redirect(url_for('view_allitems'))
            else:
                flash('could not find admin details')
                return redirect(url_for('adminpanel'))
        except Exception as e:
            print(e)
            flash('Could not delete image')
            return redirect(url_for('view_allitems'))
        else:
            flash('Item deleted successfully')
            return redirect(url_for('view_allitems'))
    else:
        flash('To delete pls login')
        return redirect(url_for('adminlogin'))
app.run(debug=True,use_reloader=True)