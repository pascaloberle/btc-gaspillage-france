import requests
import json
from datetime import date, datetime
import time

def get_current_block_height():
    """Récupère la hauteur de bloc actuelle du Bitcoin."""
    try:
        response = requests.get("https://blockstream.info/api/blocks/tip/height")
        return int(response.text)
    except Exception as e:
        print(f"Erreur lors de la récupération de la hauteur de bloc : {e}")
        return 916944  # Fallback pour 29/09/2025

def get_btc_price_eur():
    """Récupère le prix actuel du BTC en EUR via CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        return response.json()["bitcoin"]["eur"]
    except Exception as e:
        print(f"Erreur lors de la récupération du prix : {e}")
        return 97304  # Fallback pour 29/09/2025

def get_historical_prices(current_date):
    """Récupère les prix historiques BTC en EUR depuis 2018, échantillonné tous les 30 jours."""
    from_ts = 1514764800  # 2018-01-01
    to_ts = int(time.mktime(current_date.timetuple()))
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=eur&from={from_ts}&to={to_ts}"
        response = requests.get(url)
        data = response.json()['prices']
        points = []
        for i in range(0, len(data), 30):  # Échantillon tous les 30 jours
            ts_ms, p = data[i]
            dt = datetime.fromtimestamp(ts_ms / 1000).date()
            fractional_year = dt.year + ((dt.timetuple().tm_yday - 1) / 365.25)
            points.append({'x': fractional_year, 'y': p})
        return points
    except Exception as e:
        print(f"Erreur hist: {e}")
        return [{'x': 2018.0, 'y': 10000}, {'x': 2025.0, 'y': 97000}]  # Dummy fallback

def calculate_mined_btc(start_block, current_block):
    """Calcule le total de BTC minés depuis le bloc de départ jusqu'au bloc actuel."""
    total_btc = 0.0
    
    # Période 1 : Blocs ~499500 à 630000 (récompense 12.5 BTC)
    halving1_end = 630000
    blocks1 = max(0, min(halving1_end, current_block) - max(start_block, 499500))
    total_btc += blocks1 * 12.5
    
    # Période 2 : Blocs 630000 à 840000 (récompense 6.25 BTC)
    halving2_start = 630000
    halving2_end = 840000
    blocks2_start = max(start_block, halving2_start)
    blocks2_end = min(halving2_end, current_block)
    blocks2 = max(0, blocks2_end - blocks2_start)
    total_btc += blocks2 * 6.25
    
    # Période 3 : Blocs 840000 à maintenant (récompense 3.125 BTC)
    halving3_start = 840000
    blocks3_start = max(start_block, halving3_start)
    blocks3_end = current_block
    blocks3 = max(0, blocks3_end - blocks3_start)
    total_btc += blocks3 * 3.125
    
    return total_btc

def calculate_opportunity_cost(share=0.10):  # 10% de part hypothétique
    """Calcule le coût d'opportunité, plus données pour graphique."""
    start_block = 499500  # Hauteur approximative au 1er janvier 2018
    current_block = get_current_block_height()
    price_eur = get_btc_price_eur()
    current_date = date(2025, 9, 29)  # Date fixe pour cohérence avec le contexte
    
    total_mined_btc = calculate_mined_btc(start_block, current_block)
    france_btc_past = total_mined_btc * share
    value_eur_past = france_btc_past * price_eur
    total_euros_past = int(value_eur_past)  # En euros complets
    
    # Données historiques pour le graphique
    hist_points = get_historical_prices(current_date)
    
    initial_blocks = current_block - start_block
    
    return {
        'france_btc_past': france_btc_past,
        'total_euros_past': total_euros_past,
        'price_eur': price_eur,
        'share': share,
        'hist_points': hist_points,
        'initial_blocks': initial_blocks,
        'start_block': start_block,
        'initial_current_block': current_block,
        'total_mined_btc': total_mined_btc
    }

def generate_html():
    """Génère le fichier HTML avec mises à jour en temps réel via API."""
    result = calculate_opportunity_cost()
    
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horloge du Gaspillage Bitcoin - France</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Arial:wght@400;700&display=swap');
        body {{ 
            font-family: 'Arial', sans-serif; 
            background: #000; 
            color: #fff; 
            margin: 0; 
            padding: 0; 
            overflow: auto;
        }}
        .container {{ display: flex; min-height: 100vh; }}
        .left {{ 
            flex: 1; 
            padding: 40px; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            background: #000; 
        }}
        .right {{ 
            flex: 1; 
            padding: 40px; 
            background: #111; 
        }}
        h1 {{ 
            font-size: 2.5em; 
            color: #F7931A; 
            margin-bottom: 20px; 
            text-align: center;
        }}
        p {{ color: #ccc; text-align: center; margin-bottom: 40px; }}
        .counter {{ 
            font-size: 2.5em; 
            font-weight: 700; 
            margin: 20px 0; 
            padding: 20px; 
            background: rgba(247, 147, 26, 0.1); 
            border: 2px solid #F7931A; 
            border-radius: 8px; 
            box-shadow: 0 0 10px rgba(247, 147, 26, 0.3); 
            color: #fff;
            transition: all 0.3s ease;
        }}
        .label {{ 
            font-size: 1.2em; 
            color: #F7931A; 
            margin-bottom: 10px; 
            text-align: center;
        }}
        h2 {{ color: #F7931A; text-align: center; margin-bottom: 20px; }}
        #powerLawChart {{ 
            max-height: 500px; 
            background: #000; 
            border-radius: 8px; 
            border: 1px solid #F7931A; 
            margin-bottom: 20px;
        }}
        .additional-text {{ 
            color: #ccc; 
            font-size: 0.9em; 
            text-align: left; 
            line-height: 1.6;
        }}
        .additional-text ul {{ 
            list-style-type: none; 
            padding-left: 0; 
        }}
        .additional-text li {{ 
            margin-bottom: 10px; 
            padding-left: 20px; 
            position: relative; 
        }}
        .additional-text li::before {{ 
            content: "•"; 
            color: #F7931A; 
            font-weight: bold; 
            position: absolute; 
            left: 0; 
        }}
        a:link {{
            color: orange;
            background-color: transparent;
            text-decoration: none;
        }}

        a:visited {{
        color: orange;
        background-color: transparent;
        text-decoration: none;
        }}

        a:hover {{
        color: red;
        background-color: transparent;
        text-decoration: underline;
        }}

        a:active {{
        color: orange;
        background-color: transparent;
        text-decoration: underline;
        }}
        .updating {{ color: #ccc; font-size: 0.9em; text-align: center; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <h1>Horloge du Gaspillage Bitcoin - France</h1>
            <p>Coût d'opportunité si la France avait miné 10% de la puissance globale depuis 2018. Mises à jour en temps réel toutes les 10 minutes.</p>
            
            <div class="label">Total Gaspillage (€)</div>
            <div class="counter" id="totalEurosCounter">0</div>
            
            <div class="label">BTC Manqués</div>
            <div class="counter" id="btcCounter">0</div>
            
            <div class="label">Prix BTC Actuel (€)</div>
            <div class="counter" id="priceCounter">0</div>
            
            <div class="label">Blocs Manqués</div>
            <div class="counter" id="blocksCounter">0</div>
            
            <div class="updating" id="updateText">Mise à jour en temps réel via API.</div>
        </div>
        
        <div class="right">
            <h2>Prix Historique BTC (EUR)</h2>
            <canvas id="powerLawChart"></canvas>
            <div class="additional-text">
                <ul>
                    <li>Ce gaspillage n'inclut pas les potentiels retombées économiques de réindustrialiser la France avec une nouvelle industrie innovante.</li>
                    <li>La création d'emplois dans des régions rurales et là où les containers et les industriels du minage peuvent s'implémenter.</li>
                    <li>La potentielle mise en place de circularité en injectant une partie des profits dans les collectivités locales.</li>
                    <li><a href="https://cellulehumaine.substack.com/p/coming-soon">Bitcoin c'est de la science</a>, il serait temps de se remettre à la science.</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        // Fonction pour calculer les BTC minés (miroir du Python)
        function calculateMinedBtc(currentBlock) {{
            let totalBtc = 0.0;
            const startBlock = {result['start_block']};
            
            // Période 1 : ~499500 à 630000 (12.5 BTC)
            const halving1End = 630000;
            let blocks1 = Math.max(0, Math.min(halving1End, currentBlock) - Math.max(startBlock, 499500));
            totalBtc += blocks1 * 12.5;
            
            // Période 2 : 630000 à 840000 (6.25 BTC)
            const halving2Start = 630000;
            const halving2End = 840000;
            let blocks2Start = Math.max(startBlock, halving2Start);
            let blocks2End = Math.min(halving2End, currentBlock);
            let blocks2 = Math.max(0, blocks2End - blocks2Start);
            totalBtc += blocks2 * 6.25;
            
            // Période 3 : 840000+ (3.125 BTC)
            const halving3Start = 840000;
            let blocks3Start = Math.max(startBlock, halving3Start);
            let blocks3End = currentBlock;
            let blocks3 = Math.max(0, blocks3End - blocks3Start);
            totalBtc += blocks3 * 3.125;
            
            return totalBtc;
        }}

        // Animation fluide des compteurs
        function animateCounter(id, target, duration = 2000, suffix = '') {{
            const counter = document.getElementById(id);
            const start = parseFloat(counter.textContent.replace(/,/g, '').replace(/[^0-9.-]/g, '')) || 0;
            const range = target - start;
            const increment = range / (duration / 16);
            let current = start;
            const timer = setInterval(() => {{
                current += increment;
                if (current >= target) {{
                    current = target;
                    clearInterval(timer);
                }}
                if (id === 'totalEurosCounter' || id === 'btcCounter' || id === 'blocksCounter') {{
                    counter.textContent = Math.floor(current).toLocaleString() + suffix;
                }} else {{
                    counter.textContent = current.toFixed(2).toLocaleString() + suffix;
                }}
            }}, 16);
        }}

        // Données embeddées initiales
        const initialTotalEuros = {result['total_euros_past']};
        const initialBtc = {result['france_btc_past']};
        const initialPrice = {result['price_eur']};
        const initialBlocks = {result['initial_blocks']};
        const histData = {json.dumps(result['hist_points'])};
        const share = {result['share']};
        const startBlock = {result['start_block']};
        const initialCurrentBlock = {result['initial_current_block']};

        let lastHeight = initialCurrentBlock;
        let lastPrice = initialPrice;

        // Fonction de mise à jour en temps réel
        async function updateData() {{
            try {{
                const heightRes = await fetch('https://blockstream.info/api/blocks/tip/height');
                const heightText = await heightRes.text();
                const newHeight = parseInt(heightText);
                
                const priceRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur');
                const priceData = await priceRes.json();
                const newPrice = priceData.bitcoin.eur;
                
                const newTotalMined = calculateMinedBtc(newHeight);
                const newTotalBtc = newTotalMined * share;
                const newTotalEuros = Math.floor(newTotalBtc * newPrice);
                const newBlocks = newHeight - startBlock;
                
                // Animation vers les nouvelles valeurs
                animateCounter('totalEurosCounter', newTotalEuros, 1000, ' €');
                animateCounter('btcCounter', newTotalBtc, 1000, ' BTC');
                animateCounter('priceCounter', newPrice, 1000, ' €');
                animateCounter('blocksCounter', newBlocks, 1000, '');
                
                // Mise à jour du timestamp
                document.getElementById('updateText').textContent = `Dernière mise à jour: ${{new Date().toLocaleString('fr-FR')}}`;
                
                lastHeight = newHeight;
                lastPrice = newPrice;
            }} catch (e) {{
                console.error('Erreur lors de la mise à jour:', e);
            }}
        }}

        // Initialisation
        window.onload = () => {{
            // Animation initiale
            document.getElementById('totalEurosCounter').textContent = '0';
            document.getElementById('btcCounter').textContent = '0';
            document.getElementById('priceCounter').textContent = '0';
            document.getElementById('blocksCounter').textContent = '0';
            
            animateCounter('totalEurosCounter', initialTotalEuros, 3000, ' €');
            animateCounter('btcCounter', initialBtc, 3000, ' BTC');
            animateCounter('priceCounter', initialPrice, 2000, ' €');
            animateCounter('blocksCounter', initialBlocks, 2000, '');
            
            // Graphique Chart.js (historique seulement)
            const ctx = document.getElementById('powerLawChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    datasets: [
                        {{
                            label: 'Prix Historique (EUR)',
                            data: histData,
                            borderColor: '#F7931A',
                            backgroundColor: 'rgba(247, 147, 26, 0.1)',
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            type: 'linear',
                            ticks: {{ color: '#fff' }},
                            grid: {{ color: 'rgba(255,255,255,0.1)' }},
                            title: {{ display: true, text: 'Année', color: '#fff' }}
                        }},
                        y: {{
                            type: 'linear',
                            ticks: {{ color: '#fff' }},
                            grid: {{ color: 'rgba(255,255,255,0.1)' }},
                            title: {{ display: true, text: 'Prix BTC (EUR)', color: '#fff' }},
                            beginAtZero: true
                        }}
                    }},
                    plugins: {{
                        legend: {{ labels: {{ color: '#fff' }} }}
                    }}
                }}
            }});
            
            // Première mise à jour immédiate pour synchroniser
            setTimeout(updateData, 1000);
            
            // Mises à jour toutes les 10 minutes
            setInterval(updateData, 600000);
        }};
    </script>
</body>
</html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Fichier index.html généré ! Texte additionnel ajouté sous le graphique dans la partie droite, avec puces en orange Bitcoin.")

if __name__ == "__main__":
    generate_html()