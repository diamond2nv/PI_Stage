from pipython import GCSDevice
gcs = GCSDevice('C-863.10')
gcs.ConnectUSB(serialnum='0135500849')
print(gcs.qIDN())
gcs.CloseConnection()