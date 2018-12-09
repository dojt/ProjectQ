import paramiko
import user_data
import socket
import getpass
 
class KetitaSSH:
    def __init__(self):
        self.SSH_returns = []
        self.client = None
        self.host= user_data.HOST
        self.username = user_data.NAME
        self.password = user_data.PASS
        self.timeout = float(user_data.TIMEOUT)
        self.commands = user_data.COMMANDS
        self.pkey = user_data.PKEY
        self.port = user_data.PORT
        self.uploadremotefilepath = user_data.UPLOADREMOTEFILEPATH
        self.uploadlocalfilepath = user_data.UPLOADLOCALFILEPATH
        self.downloadremotefilepath = user_data.DOWNLOADREMOTEFILEPATH
        self.downloadlocalfilepath = user_data.DOWNLOADLOCALFILEPATH
 
    def connect(self):
        try:
            print("Connecting to Ketita Labs™ cloud services")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if (self.password == None):
                if (self.pkey == None):
                        self.client.connect(hostname=self.host, 
                                port=self.port,username=self.username,
                                password = getpass.getpass(prompt='Ketita Cloud password > '),
                                timeout=self.timeout, 
                                allow_agent=False, look_for_keys=False)    
                        print("Connected to Ketita Labs™ @",self.host)
                else:
                        self.pkey = paramiko.RSAKey.from_private_key_file(self.pkey)
                        self.client.connect(hostname=self.host, port=self.port, username=self.username,
                                pkey=self.pkey ,timeout=self.timeout, 
                                allow_agent=False, look_for_keys=False)
                        print("Connected to Ketita Labs™ @",self.host)
            else:
                self.client.connect(hostname=self.host, port=self.port,
                        username=self.username,password=self.password,timeout=self.timeout, 
                        allow_agent=False, look_for_keys=False)    
                print("Connected to Ketita Labs™ @",self.host)
        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials")
            result_flag = False
        except paramiko.SSHException as sshException:
            print("Could not establish SSH connection: %s" % sshException)
            result_flag = False
        except socket.timeout as e:
            print("Connection timed out")
            result_flag = False
        except Exception as e:
            print('\nException in connecting to the server')
            print('PYTHON SAYS:',e)
            result_flag = False
            self.client.close()
        else:
            result_flag = True
 
        return result_flag    
 
    def execute(self,commands):
        result_flag = True
        try:
            if self.connect():
                for command in commands:
                    print("Executing command --> {}".format(command))
                    stdin, stdout, stderr = self.client.exec_command(command,timeout=10)
                    self.SSH_returns.append([stdin, stdout, stderr])
                    if stderr.read():
                        print("Problem occurred while running command:"+ command + 
				" The error is " + stderr.read())
                        result_flag = False
                    else:    
                        print("Command execution completed successfully",command)
                        print("Output is:\n")
                        print((self.SSH_returns[-1][1].read()).decode())
                self.client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False   
        except socket.timeout as e:
            print("Command timed out.", command)
            self.client.close()
            result_flag = False                
        except paramiko.SSHException:
            print("Failed to execute the command!",command)
            self.client.close()
            result_flag = False    
 
        return result_flag
 
    def upload(self,uploadlocalfilepath,uploadremotefilepath):
        result_flag = True
        try:
            if self.connect():
                ftp_client= self.client.open_sftp()
                ftp_client.put(uploadlocalfilepath,uploadremotefilepath)
                ftp_client.close() 
                self.client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False  
        except Exception as e:
            print('\nUnable to upload the file to the remote server',uploadremotefilepath)
            print('PYTHON SAYS:',e)
            result_flag = False
            ftp_client.close()
            self.client.close()
 
        return result_flag
 
    def download(self,downloadremotefilepath,downloadlocalfilepath):
        result_flag = True
        try:
            if self.connect():
                ftp_client= self.client.open_sftp()
                ftp_client.get(downloadremotefilepath,downloadlocalfilepath)
                ftp_client.close()  
                self.client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False  
        except Exception as e:
            print('\nUnable to download the file from the remote server',downloadremotefilepath)
            print('PYTHON SAYS:',e)
            result_flag = False
            ftp_client.close()
            self.client.close()
 
        return result_flag
    
    def send_BLW(BLW_file):
        a = 1
 

if __name__=='__main__':

    connection = KetitaSSH()
    cmd = ["ls", "which python"]
    connection.execute(cmd)
