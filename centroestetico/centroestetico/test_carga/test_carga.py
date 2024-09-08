import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://gerart674.pythonanywhere.com/"  
NUM_USUARIOS = 50  # Número de usuarios simulados
NUM_REQUESTS = 10  # Número de solicitudes por usuario

def simular_usuario(user_id):
    total_time = 0
    for _ in range(NUM_REQUESTS):
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/citas/agendar/")        
        end_time = time.time()
        
        total_time += (end_time - start_time)
        
        if response.status_code != 200:
            print(f"Usuario {user_id}: Error en la solicitud - Código {response.status_code}")
    
    avg_time = total_time / NUM_REQUESTS
    print(f"Usuario {user_id}: Tiempo promedio de respuesta: {avg_time:.2f} segundos")

def ejecutar_prueba():
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=NUM_USUARIOS) as executor:
        executor.map(simular_usuario, range(NUM_USUARIOS))
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTiempo total de la prueba: {total_time:.2f} segundos")
    print(f"Solicitudes totales: {NUM_USUARIOS * NUM_REQUESTS}")
    print(f"Solicitudes por segundo: {(NUM_USUARIOS * NUM_REQUESTS) / total_time:.2f}")

if __name__ == "__main__":
    ejecutar_prueba()