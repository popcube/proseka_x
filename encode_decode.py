from cryptography.fernet import Fernet
import os

key = os.environ.get("CSV_KEY")
enc_dec = os.environ.get("ENC_DEC")
fernet = Fernet(key)

def enc():
  with open('./docs/sorted_data.csv', 'rb') as file:
    original = file.read()

  encrypted = fernet.encrypt(original)

  with open('./docs/sorted_data.csv', 'wb') as file:
    file.write(encrypted)

def dec():
  with open('./docs/sorted_data.csv', 'rb') as file:
    encrypted = file.read()

  decrypted = fernet.decrypt(encrypted)

  with open('./docs/sorted_data.csv', 'wb') as file:
    file.write(decrypted)
    
if __name__ == '__main__':
  if enc_dec == "ENC":
    enc()
  if enc_dec == "DEC":
    dec()
        