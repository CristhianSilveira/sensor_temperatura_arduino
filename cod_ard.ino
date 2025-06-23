#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <math.h>

// Definições dos pinos do Arduino conectados ao display
#define TFT_CS    10  // Chip Select (CS)
#define TFT_DC    9   // Data/Command (DC)
#define TFT_RST   8   // Reset (RST)

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

// Pino analógico onde o termistor está conectado
const int pinoNTC = A5;

const float R_SERIE = 10000.0; // Resistência do resistor em SÉRIE com 10kΩ.
const float BETA = 4000.0;
const float T0 = 298.15;
const float R0 = 10000.0;

void setup() {
  Serial.begin(9600);

  tft.init(240, 320);         // Display com sua resolução
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK); // Toda a tela com a cor preta
  tft.setTextColor(ST77XX_GREEN); // Cor do texto para verde
  tft.setTextSize(2);

  tft.setCursor(50, 50);     // Define a posição do cursor (coluna, linha)
  tft.print("Iniciando...");
  delay(1000);
}


void loop() {
  int leitura = analogRead(pinoNTC);

  //Converte a leitura analógica para uma tensão (em Volts)
  float tensao = leitura * 5.0 / 1023.0;

  // Cálculo da Resistência do Termistor (Rntc)
  float Rntc = (5.0 * R_SERIE / tensao) - R_SERIE;

  float tempK = 1.0 / (1.0 / T0 + (1.0 / BETA) * log(Rntc / R0));
  
  // Converte a temperatura de Kelvin para Celsius
  float tempC = tempK - 273.15;

  // Envio da Temperatura para o Computador (Interface Python) via Porta Serial
  Serial.print("TEMP:");
  Serial.println(tempC, 2);

  // Exibir Temperatura no Display
  tft.fillRect(30, 100, 200, 40, ST77XX_BLACK);
  tft.setCursor(30, 100);    // Define a posição onde o texto começará a ser exibido
  tft.print("Temp: ");
  tft.print(tempC, 2);
  tft.println(" C");

  delay(1000);
}