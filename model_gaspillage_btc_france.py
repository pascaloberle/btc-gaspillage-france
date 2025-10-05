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

def get_current_hash_rate_ths():
    """Récupère le hash rate actuel en TH/s via Blockchain.info API."""
    try:
        response = requests.get("https://api.blockchain.info/charts/hash-rate?format=json")
        data = response.json()
        hr_ths = data['values'][-1]['y']
        return hr_ths
    except Exception as e:
        print(f"Erreur lors de la récupération du hash rate : {e}")
        return 600000000  # Fallback approx 600 EH/s = 6e8 TH/s

def days_since_genesis(current_date=None):
    """Calcule les jours depuis la genèse (03/01/2009)."""
    genesis = date(2009, 1, 3)
    if current_date is None:
        current_date = date.today()
    return (current_date - genesis).days

def get_historical_prices(current_date):
    """Récupère les prix historiques BTC en EUR depuis 2018, échantillonné tous les 7 jours pour hebdomadaire."""
    from_ts = 1514764800  # 2018-01-01
    to_ts = int(time.mktime(current_date.timetuple()))
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=eur&from={from_ts}&to={to_ts}"
        response = requests.get(url)
        data = response.json()['prices']
        points = []
        for i in range(0, len(data), 7):  # Échantillon tous les 7 jours pour hebdomadaire
            ts_ms, p = data[i]
            dt = datetime.fromtimestamp(ts_ms / 1000).date()
            fractional_year = dt.year + ((dt.timetuple().tm_yday - 1) / 365.25)
            points.append({'x': fractional_year, 'y': p})
        return points
    except Exception as e:
        print(f"Erreur hist: {e}")
        return [{'x': 2018.0, 'y': 10000}, {'x': 2025.0, 'y': 97000}]  # Dummy fallback

def get_power_law_points(current_date, exponent=5.8, years_ahead=5):
    """Génère des points pour la courbe de loi de puissance."""
    current_days = days_since_genesis(current_date)
    price_eur = get_btc_price_eur()
    A = price_eur / (current_days ** exponent)
    
    points = []
    for i in range(0, (years_ahead * 365) + 1, 30):  # Tous les 30 jours pour lisser
        day = current_days + i
        year = 2009 + (day / 365.25)
        price = A * (day ** exponent)
        points.append({'x': year, 'y': price})
    return points, A, exponent

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

def calculate_opportunity_cost(share=0.03):  # 3% de part hypothétique
    """Calcule le coût d'opportunité, plus données pour graphique."""
    start_block = 499500  # Hauteur approximative au 1er janvier 2018
    current_block = get_current_block_height()
    price_eur = get_btc_price_eur()
    current_date = date.today()
    
    total_mined_btc = calculate_mined_btc(start_block, current_block)
    france_btc_past = total_mined_btc * share
    value_eur_past = france_btc_past * price_eur
    total_euros_past = int(value_eur_past)  # En euros complets
    
    # Données historiques pour le graphique
    hist_points = get_historical_prices(current_date)
    
    initial_blocks = current_block - start_block
    
    # Calcul initial MW/jour total réseau (puissance moyenne)
    hr_ths = get_current_hash_rate_ths()
    eff = 30  # J/TH moyenne
    total_power_w = hr_ths * eff
    total_mw = total_power_w / 1_000_000
    
    # Points pour loi de puissance
    power_points, A, exponent = get_power_law_points(current_date)
    
    return {
        'france_btc_past': france_btc_past,
        'total_euros_past': total_euros_past,
        'price_eur': price_eur,
        'share': share,
        'hist_points': hist_points,
        'initial_blocks': initial_blocks,
        'start_block': start_block,
        'initial_current_block': current_block,
        'total_mined_btc': total_mined_btc,
        'initial_total_mw': total_mw,
        'power_points': power_points,
        'A': A,
        'exponent': exponent
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
    <title>Compteur Bitcoin France</title>
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
        .share-select {{ 
            font-size: 1.2em; 
            color: #F7931A; 
            background: rgba(247, 147, 26, 0.1); 
            border: 2px solid #F7931A; 
            border-radius: 8px; 
            padding: 10px; 
            margin-bottom: 20px; 
            text-align: center;
        }}
        /* Style the button that is used to open and close the collapsible content */
        .collapsible {{
        background-color: #000;
        color: orange;
        cursor: pointer;
        padding: 25px;
        width: 80%;
        border: none;
        text-align: left;
        outline: none;
        font-size: 15px;
        }}

        /* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
        .active, .collapsible:hover {{
        background-color: #000;
        }}

        /* Style the collapsible content. Note: hidden by default */
        .collapsible-content {{
        padding: 0 18px;
        display: none;
        overflow: hidden;
        background-color: #000;
        }}

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
            <h1>Compteur Bitcoin France</h1>
            <p>Coût d'opportunité si la France avait miné X% (sélectionnable ci-dessous) de la puissance globale de hachage du réseau Bitcoin depuis 2018. Mises à jour en temps réel toutes les 10 minutes.</p>
            
            <select id="shareSelect" class="share-select">
                <option value="1">1%</option>
                <option value="2">2%</option>
                <option value="3" selected>3%</option>
                <option value="5">5%</option>
                <option value="10">10%</option>
                <option value="15">15%</option>
            </select>
            
            <div class="label">MW/Jour Nécessaires</div>
            <div class="counter" id="mwhCounter">0</div>

            <div class="label">Total Manqués (€)</div>
            <div class="counter" id="totalEurosCounter">0</div>
            
            <div class="label">BTC Manqués</div>
            <div class="counter" id="btcCounter">0</div>
            
            <div class="label">Prix BTC Actuel (€)</div>
            <div class="counter" id="priceCounter">0</div>
            
            <div class="label">Blocs Manqués</div>
            <div class="counter" id="blocksCounter">0</div>
            
            
            
            <div class="updating" id="updateText">Mise à jour en temps réel.</div>
        </div>
        
        <div class="right">
            <h2>Prix Historique BTC (EUR) & Loi de Puissance (exposant 5.8)</h2>
            <canvas id="powerLawChart"></canvas>
            <div class="additional-text">
                <ul>
                    <li>Ce manque à gagner n'inclut pas les potentielles retombées économiques de réindustrialiser la France avec une nouvelle industrie novatrice.</li>
                    <li>La création d'emplois dans des régions rurales et là où les containers de minage peuvent s'implémenter.</li>
                    <li>La potentielle mise en place de circularité en injectant une partie des profits dans les collectivités locales.</li>
                    <li>Pour maximiser l'utilité du minage de Bitcoin dans la société : les profits du minage pourraient servir au bien-être des populations, au développement des énergies renouvelables, à l'agroécologie et à aider à la transition bas-carbone des pays du Sud par exemple.</li>
                    <li><a href="https://x.com/i/grok/share/vxt7T2ufIWKKPaWyWEj0I5Mtl" target="_blank">Le Bitcoin peut devenir un grand allié pour accélérer la transition énergétique</a>. Mais il faut interdire l’utilisation de combustible fossile dans le minage Bitcoin sous peine de lourdes sanctions et réguler le minage pour que l'usage n'empiète pas sur la consommation d'électricité courante (optimisation sous contraintes).</li>
                    <li><a href="https://b1m.io/" target="_blank">Bitcoin suit une loi de puissance</a> et le rendement futur pourrait être projeté avec un écart type d'erreur.</li>
                    <li>En apprendre plus sur Bitcoin avec <a href="https://tinyurl.com/viebitcoin" target="_blank">un article scientifique qui lui est dédié</a>.</li>
                </ul>
                <br />
                <button type="button" class="collapsible">Cliquez ici pour plus d'explications techniques sur le script.</button>
                <div class="collapsible-content">
                    <ul>
                        <li>Ce script calcule le potentiel manqué en milliards d'euros à miner Bitcoin depuis le 1er Janvier 2018. Il suppose que la France aurait pu dédier une part fixe (1,2,3,5,10 ou 15%) de la puissance de hachage globale du réseau Bitcoin depuis janvier 2018 (une hypothèse réaliste avec différents scénarios et basée sur une estimation d'électricité consommé globalement du Bitcoin ~500 TWh cumulés sur la période). Il fetch les données en temps réel (hauteur de bloc actuelle et prix du BTC en EUR) via des API gratuites. Le total est le nombre de BTC minés multiplié par le prix actuel, converti en milliards d'EUR.</li>
                        <li>Récupération en temps réel : Toutes les 10 minutes (600 000 ms), le JS fetch les données via les API (hauteur de bloc via Blockstream et prix via CoinGecko). Les API sont gratuites et CORS-compatibles.</li>
                        <li>Calculs dynamiques : J'ai intégré une fonction JS calculateMinedBtc qui miroite le calcul Python pour déterminer les BTC minés cumulés (en tenant compte des halvings). Le total gaspillage est recalculé comme (BTC # manqués totaux × prix actuel), et les compteurs s'animent vers les nouvelles valeurs.</li>  
                        <li>Ceci est une simulation, <a href="https://colab.research.google.com/drive/1OC5ePgAxMX47JP14uQVTpBktjd2kZq6u?usp=sharing" target="_blank">j'ouvre le code source pour rendre la logique transparente</a>. Cette simulation peut donner une idée de "l'ordre de grandeur" et un rendement total brut sans pour autant prendre en compte CAPEX et autres considérations techniques et implémentations fines.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {{
        coll[i].addEventListener("click", function() {{
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "block") {{
            content.style.display = "none";
            }} else {{
            content.style.display = "block";
            }}
        }});
        }}
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
                if (id === 'totalEurosCounter' || id === 'btcCounter' || id === 'blocksCounter' || id === 'mwhCounter') {{
                    counter.textContent = Math.floor(current).toLocaleString() + suffix;
                }} else {{
                    counter.textContent = current.toFixed(2).toLocaleString() + suffix;
                }}
            }}, 16);
        }}

        // Fonction pour mettre à jour tous les compteurs avec le share actuel
        function updateAllCounters(newHeight, newPrice, newBlocks, totalMw) {{
            const share = currentShare / 100;
            const newTotalMined = calculateMinedBtc(newHeight);
            const newTotalBtc = newTotalMined * share;
            const newTotalEuros = Math.floor(newTotalBtc * newPrice);
            const newMw = totalMw * share;
            
            animateCounter('totalEurosCounter', newTotalEuros, 1000, ' €');
            animateCounter('btcCounter', newTotalBtc, 1000, ' BTC');
            animateCounter('priceCounter', newPrice, 1000, ' €');
            animateCounter('blocksCounter', newBlocks, 1000, '');
            animateCounter('mwhCounter', newMw, 1000, ' MW');
        }}

        // Données embeddées initiales
        const initialTotalEuros = {result['total_euros_past']};
        const initialBtc = {result['france_btc_past']};
        const initialPrice = {result['price_eur']};
        const initialBlocks = {result['initial_blocks']};
        const histData = {json.dumps(result['hist_points'])};
        const powerData = {json.dumps(result['power_points'])};
        const initialTotalMw = {result['initial_total_mw']};
        const startBlock = {result['start_block']};
        const initialCurrentBlock = {result['initial_current_block']};

        let currentShare = 3;
        let lastHeight = initialCurrentBlock;
        let lastPrice = initialPrice;
        let lastTotalMw = initialTotalMw;

        // Événement pour le dropdown
        document.getElementById('shareSelect').onchange = function(e) {{
            currentShare = parseInt(e.target.value);
            // Mise à jour immédiate avec les dernières données connues
            if (lastHeight && lastPrice) {{
                fetch('https://api.blockchain.info/charts/hash-rate?format=json&cors=true')
                .then(r => r.json())
                .then(hashData => {{
                    const hr_ths = hashData.values[hashData.values.length - 1].y;
                    const eff = 30; // J/TH moyenne
                    const total_power_w = hr_ths * eff;
                    const total_mw = total_power_w / 1000000;
                    updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, total_mw);
                    lastTotalMw = total_mw;
                }})
                .catch(() => {{
                    // Fallback avec valeur initiale
                    updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, initialTotalMw);
                }});
            }}
        }};

        // Fonction de mise à jour en temps réel
        async function updateData() {{
            try {{
                const heightRes = await fetch('https://blockstream.info/api/blocks/tip/height');
                const heightText = await heightRes.text();
                const newHeight = parseInt(heightText);
                
                const priceRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur');
                const priceData = await priceRes.json();
                const newPrice = priceData.bitcoin.eur;
                
                // Fetch hash rate pour MW
                const hrRes = await fetch('https://api.blockchain.info/charts/hash-rate?format=json&cors=true');
                const hashData = await hrRes.json();
                const hr_ths = hashData.values[hashData.values.length - 1].y;
                const eff = 30; // J/TH moyenne réseau
                const total_power_w = hr_ths * eff;
                const total_mw = total_power_w / 1000000;
                
                const newBlocks = newHeight - startBlock;
                
                // Mise à jour avec share actuel
                updateAllCounters(newHeight, newPrice, newBlocks, total_mw);
                
                // Mise à jour du timestamp
                document.getElementById('updateText').textContent = `Dernière mise à jour: ${{new Date().toLocaleString('fr-FR')}}`;
                
                lastHeight = newHeight;
                lastPrice = newPrice;
                lastTotalMw = total_mw;
            }} catch (e) {{
                console.error('Erreur lors de la mise à jour:', e);
                // Fallback
                updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, lastTotalMw);
            }}
        }}

        // Initialisation
        window.onload = () => {{
            // Animation initiale avec share=10
            const initialShare = 0.03;
            const initialMw = initialTotalMw * initialShare;
            
            document.getElementById('totalEurosCounter').textContent = '0';
            document.getElementById('btcCounter').textContent = '0';
            document.getElementById('priceCounter').textContent = '0';
            document.getElementById('blocksCounter').textContent = '0';
            document.getElementById('mwhCounter').textContent = '0';
            
            animateCounter('totalEurosCounter', initialTotalEuros, 3000, ' €');
            animateCounter('btcCounter', initialBtc, 3000, ' BTC');
            animateCounter('priceCounter', initialPrice, 2000, ' €');
            animateCounter('blocksCounter', initialBlocks, 2000, '');
            animateCounter('mwhCounter', initialMw, 2000, ' MW');
            
            // Graphique Chart.js avec historique et loi de puissance
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
                        }},
                        {{
                            label: 'Loi de Puissance (exposant 5.8)',
                            data: powerData,
                            borderColor: '#FF6B35',
                            backgroundColor: 'transparent',
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false,
                            borderDash: [5, 5]
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
            
            // Mises à jour toutes les minutes
            setInterval(updateData, 600000);
        }};
    </script>
</body>
</html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Fichier index.html généré ! Graphique modifié : Ajout d'une courbe de loi de puissance (exposant 5.8) en pointillé orange clair, projetée sur 5 ans. Historique conservé en continu. Titre du graphique mis à jour.")

if __name__ == "__main__":
    generate_html()
