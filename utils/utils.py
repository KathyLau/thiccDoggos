def getSecretData():
    #get data
    secrets = open("secrets.txt", "r")
    secretsRaw = secrets.read()

    #split it up
    secretsArray = secretsRaw.split("\n")

    #make it easily accessible
    secretsDictionary = {
        'email': secretsArray[0],
        'email-password': secretsArray[1],
        'app-secret-key': secretsArray[2]
    }

    return secretsDictionary
