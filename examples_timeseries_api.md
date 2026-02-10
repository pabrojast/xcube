# xcube Timeseries API - Ejemplos de Uso

Base URL: `https://data.dev-wins.com/xcube`

## 1. Serie Temporal para un Punto

```bash
curl -X POST "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq100_pyramid/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Point",
    "coordinates": [30.5, 50.5]
  }'
```

**Nota:** Las coordenadas deben estar en el CRS del dataset (generalmente lon, lat)

## 2. Serie Temporal para un Polígono (con agregación)

```bash
curl -X POST "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq100_pyramid/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Polygon",
    "coordinates": [[
      [30.0, 50.0],
      [31.0, 50.0],
      [31.0, 51.0],
      [30.0, 51.0],
      [30.0, 50.0]
    ]]
  }'
```

## 3. Serie Temporal con filtro de tiempo

```bash
curl -X POST "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq100_pyramid/chla_mean?startDate=2024-09-01&endDate=2024-12-31" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Point",
    "coordinates": [30.5, 50.5]
  }'
```

## 4. Serie Temporal con método de agregación específico

```bash
# Para polígonos, puedes especificar el método de agregación
curl -X POST "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq100_pyramid/turbidity_mean?aggMethods=mean,min,max" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Polygon",
    "coordinates": [[
      [30.0, 50.0],
      [31.0, 50.0],
      [31.0, 51.0],
      [30.0, 51.0],
      [30.0, 50.0]
    ]]
  }'
```

## 5. Usando Python

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

base_url = "https://data.dev-wins.com/xcube"

# Definir geometría (punto)
geometry = {
    "type": "Point",
    "coordinates": [30.5, 50.5]
}

# Hacer request
dataset = "ukraine_lwq100_pyramid"
variable = "turbidity_mean"

response = requests.post(
    f"{base_url}/timeseries/{dataset}/{variable}",
    json=geometry,
    params={
        "startDate": "2024-09-01",
        "endDate": "2025-09-01"
    }
)

data = response.json()

# Convertir a DataFrame
df = pd.DataFrame(data['result'])
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# Eliminar valores nulos
df = df.dropna()

# Visualizar
if not df.empty:
    df.plot(y='mean', title=f'{variable} Time Series', figsize=(12, 6))
    plt.ylabel(variable)
    plt.grid(True)
    plt.show()
else:
    print("No data found for this location")
```

## 6. Script Python para extraer datos de múltiples variables

```python
import requests
import pandas as pd

def get_timeseries(dataset, variable, lon, lat, start_date=None, end_date=None):
    """
    Extrae serie temporal de xcube para un punto específico
    """
    base_url = "https://data.dev-wins.com/xcube"
    
    geometry = {
        "type": "Point",
        "coordinates": [lon, lat]
    }
    
    params = {}
    if start_date:
        params['startDate'] = start_date
    if end_date:
        params['endDate'] = end_date
    
    response = requests.post(
        f"{base_url}/timeseries/{dataset}/{variable}",
        json=geometry,
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['result'])
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        df.columns = [variable]
        return df
    else:
        print(f"Error: {response.status_code}")
        return None

# Ejemplo de uso: extraer múltiples variables
dataset = "ukraine_lwq100_pyramid"
lon, lat = 30.5, 50.5

variables = ['turbidity_mean', 'chla_mean', 'Rw490_rep', 'Rw560_rep']

dfs = []
for var in variables:
    df = get_timeseries(dataset, var, lon, lat, 
                       start_date="2024-09-01", 
                       end_date="2025-09-01")
    if df is not None and not df.empty:
        dfs.append(df)

# Combinar todas las variables
if dfs:
    combined_df = pd.concat(dfs, axis=1)
    print(combined_df)
    
    # Guardar a CSV
    combined_df.to_csv('ukraine_lwq_timeseries.csv')
    
    # Graficar
    combined_df.plot(subplots=True, figsize=(12, 10), title='Ukraine LWQ Time Series')
    plt.tight_layout()
    plt.savefig('timeseries.png')
    plt.show()
```

## 7. Para extraer datos de área (con estadísticas)

```python
import requests

# Definir área de interés (bounding box como polígono)
geometry = {
    "type": "Polygon",
    "coordinates": [[
        [30.0, 50.0],  # lon, lat
        [31.0, 50.0],
        [31.0, 51.0],
        [30.0, 51.0],
        [30.0, 50.0]
    ]]
}

response = requests.post(
    "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq100_pyramid/turbidity_mean",
    json=geometry,
    params={"aggMethods": "mean,min,max,std"}
)

data = response.json()
df = pd.DataFrame(data['result'])
print(df)
```

## Parámetros disponibles:

- `startDate`: Fecha inicio (ISO 8601): `2024-09-01`
- `endDate`: Fecha fin (ISO 8601): `2025-09-01`
- `aggMethods`: Métodos de agregación (para polígonos): `mean`, `min`, `max`, `std`, `median`
- `maxValids`: Máximo número de valores válidos a retornar

## Datasets disponibles:

- `ukraine_lwq100_pyramid` - LWQ100 MSI (Sentinel-2)
  - Variables: turbidity_mean, chla_mean, Rw490_rep, Rw560_rep, Rw665_rep, Rw842_rep, Rw1610_rep, Rw2190_rep

- `ukraine_lwq300_pyramid` - LWQ300 OLCI (Sentinel-3)
  - Variables: trsp_mean, tsm_mean, Rw400_rep, Rw412p5_rep, Rw442p5_rep, Rw510_rep, Rw620_rep, Rw681_rep, Rw709_rep

## Formato de respuesta:

```json
{
  "result": [
    {
      "mean": 12.5,
      "time": "2024-09-01T00:00:00Z"
    },
    {
      "mean": 15.3,
      "time": "2024-09-11T00:00:00Z"
    }
  ]
}
```

## Notas importantes:

1. Las coordenadas en GeoJSON son **[lon, lat]**, no [lat, lon]
2. Los valores `null` indican que no hay datos para esa ubicación/tiempo
3. Para polígonos, el primer y último punto deben ser el mismo (cerrar el polígono)
4. Los datos son composiciones de 10 días, por lo que las fechas son cada 10 días aproximadamente
