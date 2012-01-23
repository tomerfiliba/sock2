import sock2

s1 = sock2.TcpListener("localhost", 11223)
s2 = sock2.TcpSocket("localhost", 11223)
s3 = s1.accept()

s2.send("hello")
assert s3.recv(100) == "hello"

s3.send("world")
assert s2.recv(100) == "world"





