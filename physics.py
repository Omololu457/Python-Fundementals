from dotenv import load_dotenv
import os

print(os.environ)
load_dotenv()
print(os.environ)
print(type(os.getenv("G1")))

print("all mesurements must be in KG")
C = float(os.getenv("C"))
G = float(os.getenv("G1")) * float(os.getenv("G2") )** float((os.getenv("G3")))
M = float(input("what is your mass: "))
RT = 2*(G*(M))
RB =C ** 2
R = RT/RB
print(f"This is your schwarzschild {R}, the amount of space you would"
      f" need to compress {M} KG to turn it into a non rotating black hole")