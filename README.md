# Compteur Bitcoin Gaspillage France
- Récupération en temps réel : Toutes les 10 minutes (600 000 ms), le JS fetch les données via les API (hauteur de bloc via Blockstream et prix via CoinGecko). Les API sont gratuites et CORS-compatibles.
- Calculs dynamiques : J'ai intégré une fonction JS calculateMinedBtc qui miroite le calcul Python pour déterminer les BTC minés cumulés (en tenant compte des halvings). Le total gaspillage est recalculé comme (BTC # manqués totaux × prix actuel), et les compteurs s'animent vers les nouvelles valeurs.


