#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <AHT10.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <LoRa.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>   

// Configuración de pines
#define TFT_CS    5
#define TFT_RST   16
#define TFT_DC    17
#define LORA_SCK  18
#define LORA_MISO 19
#define LORA_MOSI 23
#define LORA_CS   5
#define LORA_RST  14
#define LORA_IRQ  26
#define RELE_LED 25
#define RELE_BOMBA 26
#define TRIGGER 4
#define ECHO 2
#define DISTANCIA_MINIMA_AGUA 10
#define LDR 8
#define HumSueloRES 10
#define HumSueloCAP 11

// Wi-Fi
const char* ssid = "DZS_5380";
const char* password = "dzsi123456789";
const char* serverName = "http://192.168.55.104/api";  // URL del servidor para enviar los datos

// (Ya no definimos nodoID de forma fija; el id de cada nodo hijo vendrá en su mensaje)

// Configuración BLE
#define SERVICE_UUID        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BLECharacteristic *pCharacteristic;
bool dataReceived = false;
String bleData = "";

// Configuración LoRa
String loraData = "";
bool loraDataReceived = false;

// Variables de sensores
float temperatura, humedad, luzAmbiente;
int nivelAgua, humedadSueloCap, humedadSueloRes, distancia, Reintentos = 5;
bool Iluminacion, Bomba, loRaConectado;

// Pantalla y sensores
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);
AHT10 aht10;

// Variable global para el id del gateway (obtenido del Chip ID / MAC)
String gatewayID;

// Función para inicializar Wi-Fi
void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando a Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println(" Conectado a Wi-Fi.");
}

// Función para enviar datos al servidor usando JSON
void enviarDatosServidor(String childID, float temp, float hum, int nivelAgua, float luz, int humCap, int humRes) {
  const int reintentos = 5;
  int attempt = 0;
  bool enviadoConExito = false;
  
  while (attempt < reintentos && !enviadoConExito) {
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");
      
      // Construir el payload JSON
      StaticJsonDocument<256> doc;
      doc["child_id"] = childID;
      
      JsonObject sensorData = doc.createNestedObject("sensor_data");
      sensorData["temp"] = temp;
      sensorData["hum"] = hum;
      sensorData["luz"] = luz;
      sensorData["hum_cap"] = humCap;
      sensorData["hum_res"] = humRes;
      sensorData["nivel_agua"] = nivelAgua;
      
      doc["gateway_id"] = gatewayID;
      // Utilizamos millis() como timestamp; si tienes un NTP sincronizado, usa time()
      doc["timestamp"] = millis();
      
      String postData;
      serializeJson(doc, postData);
      
      int httpResponseCode = http.POST(postData);
      
      if (httpResponseCode == 200) {  
        String response = http.getString();
        if (response.indexOf("confirmado") >= 0 || response.length() > 0) {
          Serial.println("Datos enviados correctamente.");
          enviadoConExito = true;
        } else {
          Serial.println("No se recibió confirmación adecuada, reintentando...");
        }
      } else {
        Serial.println("Intento " + String(attempt + 1) + " fallido, código: " + String(httpResponseCode));
      }
      http.end();
    } else {
      Serial.println("No conectado a Wi-Fi, reintentando...");
    }
    attempt++;
    if (!enviadoConExito) {
      delay(2000);
    }
  }
  
  if (!enviadoConExito) {
    Serial.println("Error: No se pudo enviar los datos tras " + String(reintentos) + " intentos.");
  }
}

// Función para medir el nivel de agua con HC-SR04
int medirNivelAgua() {
  digitalWrite(TRIGGER, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER, LOW);

  long duracion = pulseIn(ECHO, HIGH);
  int distancia = duracion * 0.034 / 2;
  return distancia;
}

// Procesar datos recibidos vía BLE ( envía en formato JSON)

void procesarDatosBLE() {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, bleData);
  if (error) {
    Serial.print("Error al parsear JSON: ");
    Serial.println(error.f_str());
    return;
  }
  
  const char* child_id = doc["id"];
  float temp = doc["temp"];
  float hum = doc["hum"];
  float luz = doc["luz"];
  int hum_cap = doc["hum_cap"];
  int hum_res = doc["hum_res"];
  int nivel = doc["nivel_agua"];
  
  Serial.print("Datos BLE recibidos del nodo: ");
  Serial.println(child_id);
  
  // Enviar datos al servidor en formato JSON (incluye gateway_id)
  enviarDatosServidor(String(child_id), temp, hum, nivel, luz, hum_cap, hum_res);
}

// Similarmente para LoRa, se asume que el mensaje se recibe en formato JSON.
void procesarDatosLoRa() {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, loraData);
  if (error) {
    Serial.print("Error al parsear JSON (LoRa): ");
    Serial.println(error.f_str());
    return;
  }
  
  const char* child_id = doc["id"];
  float temp = doc["temp"];
  float hum = doc["hum"];
  float luz = doc["luz"];
  int hum_cap = doc["hum_cap"];
  int hum_res = doc["hum_res"];
  int nivel = doc["nivel_agua"];
  
  Serial.print("Datos LoRa recibidos del nodo: ");
  Serial.println(child_id);
  
  enviarDatosServidor(String(child_id), temp, hum, nivel, luz, hum_cap, hum_res);
}

void enviarConfirmacion(String idNodo) {
  String mensaje = "Datos recibidos correctamente del nodo: " + idNodo;
  // Enviar mensaje de confirmación vía BLE (ejemplo comentado)
  // pCharacteristic->setValue(mensaje.c_str());
  // pCharacteristic->notify();
  // Serial.println("Confirmación enviada al nodo: " + idNodo);
}

void controlBomba() {
  nivelAgua = medirNivelAgua();
  if (nivelAgua < DISTANCIA_MINIMA_AGUA) {
    digitalWrite(RELE_BOMBA, HIGH);
    Bomba = true;
    Serial.println("Bomba activada.");
  } else {
    digitalWrite(RELE_BOMBA, LOW);
    Bomba = false;
    Serial.println("Bomba desactivada.");
  }
}

void leerHumedadSuelo() {
  humedadSueloCap = analogRead(HumSueloCAP);
  humedadSueloRes = analogRead(HumSueloRES);
  Serial.print("Humedad Suelo Capacitivo: ");
  Serial.println(humedadSueloCap);
  Serial.print("Humedad Suelo Resistivo: ");
  Serial.println(humedadSueloRes);
}

void setupDisplay() {
  Wire.begin();
  aht10.begin();
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextWrap(true);
  tft.setTextSize(1);
  tft.println("Nodo_1");
}

// Función para medir nivel de agua (alternativa)
int MedirNivelAgua() {
  digitalWrite(TRIGGER, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER, LOW);
  long duracion = pulseIn(ECHO, HIGH);
  return duracion * 0.034 / 2;
}

float leerLuzAmbiente() {
  int lecturaLDR = analogRead(LDR);
  float luz = (lecturaLDR / 4095.0) * 100.0;
  Serial.print("Luz Ambiente: ");
  Serial.println(luz);
  return luz;
}

void controlIluminacion() {
  luzAmbiente = leerLuzAmbiente();
  if (luzAmbiente < 20.0) {
    digitalWrite(RELE_LED, HIGH);
    Iluminacion = true;
    Serial.println("Iluminación activada.");
  } else {
    digitalWrite(RELE_LED, LOW);
    Iluminacion = false;
    Serial.println("Iluminación desactivada.");
  }
}

bool iniciarLoRa() {
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  for (int i = 0; i < Reintentos; i++) {
    if (LoRa.begin(915E6)) {
      Serial.println("Sistema LoRa listo.");
      loRaConectado = true;
      return true;
    } else {
      Serial.println("Fallo al iniciar LoRa. Intentando de nuevo...");
      delay(1000);
    }
  }
  Serial.println("No se pudo iniciar LoRa tras varios intentos. Continuando sin LoRa...");
  loRaConectado = false;
  return false;
}

void verificarConexionLoRa() {
  if (!loRaConectado) {
    Serial.println("Verificando conexión LoRa...");
    if (iniciarLoRa()) {
      Serial.println("LoRa reconectado.");
    }
  }
}

// Callback BLE para recibir datos en formato JSON
class MyCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    bleData = pCharacteristic->getValue().c_str();
    if (bleData.length() > 0) {
      dataReceived = true;
    }
  }
};

void setup() {
  Serial.begin(9600);
  
  // Asignar el ID del gateway usando el Chip ID (MAC)
  gatewayID = String((uint64_t)ESP.getEfuseMac(), HEX);
  Serial.print("Gateway ID: ");
  Serial.println(gatewayID);
  
  // Inicializar pantalla
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(2);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(0, 0);
  tft.println("iniciando...");
  
  // Configurar Wi-Fi
  setupWiFi();
  
  // Configurar LoRa
  iniciarLoRa();
  
  // Configurar BLE
  BLEDevice::init("nodo central cultivo");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );
  pCharacteristic->setCallbacks(new MyCallbacks());
  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
}

void loop() {
  // Procesar datos recibidos por BLE (en formato JSON)
  if (dataReceived) {
    procesarDatosBLE();
    dataReceived = false;
  }

  // Procesar datos recibidos por LoRa (en formato JSON)
  if (loraDataReceived) {
    procesarDatosLoRa();
    loraDataReceived = false;
  }
  
  Serial.println("=========== ESTADO DE CONEXIONES ===========");
  Serial.print("Wi-Fi: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "Conectado" : "No conectado");
  
  Serial.print("BLE: ");
  Serial.println(dataReceived ? "Nodo conectado" : "No conectado");
  
  Serial.print("LoRa: ");
  Serial.println(loraDataReceived ? "Datos recibidos" : "Esperando datos");
  
  // Verificar conexión LoRa
  verificarConexionLoRa();
  
  Serial.println("=========== DATOS DE LOS SENSORES ===========");
  Serial.print("Temperatura: ");
  Serial.println(temperatura);
  Serial.print("Humedad: ");
  Serial.println(humedad);
  Serial.print("Luz Ambiente: ");
  Serial.println(luzAmbiente);
  Serial.print("Nivel de Agua: ");
  Serial.println(nivelAgua);
  Serial.print("Humedad Suelo (Capacitivo): ");
  Serial.println(humedadSueloCap);
  Serial.print("Humedad Suelo (Resistivo): ");
  Serial.println(humedadSueloRes);
  
  Serial.println("=========== ESTADO DE ACTUADORES ===========");
  Serial.print("Iluminación: ");
  Serial.println(Iluminacion);
  Serial.print("Bomba: ");
  Serial.println(Bomba);
  Serial.println("=============================================");
  
  delay(120000); //aguarda 2 minutos hasta la prox medicion 
}
