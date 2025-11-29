import streamlit as st
from utils.logger import setup_logger
from utils.i18n import language_selector, t, get_language

logger = setup_logger(__name__)

st.set_page_config(page_title=t("page_glossary"), layout="wide", page_icon="📖")

# Selector de idioma
language_selector()

lang = get_language()

st.title("📖 " + t("glossary_title"))
st.markdown(t("glossary_subtitle"))

# Tabs principales
if lang == 'es':
    tab_glosario, tab_tecnico, tab_disclaimers = st.tabs([
        "📚 Glosario de Métricas", 
        "🔧 Conceptos Técnicos", 
        "⚠️ Limitaciones y Uso Responsable"
    ])
else:
    tab_glosario, tab_tecnico, tab_disclaimers = st.tabs([
        "📚 Metrics Glossary", 
        "🔧 Technical Concepts", 
        "⚠️ Limitations and Responsible Use"
    ])

# ==================== TAB 1: GLOSARIO ====================
with tab_glosario:
    if lang == 'es':
        st.header("📊 Glosario de Métricas")
        
        st.markdown("""
        ---
        ### Métricas Ofensivas
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **xG (Expected Goals)**  
            Goles esperados según la calidad de las oportunidades generadas. Un xG de 0.8 significa que, 
            en promedio, esa ocasión termina en gol el 80% de las veces.
            
            **xA (Expected Assists)**  
            Asistencias esperadas según la calidad de los pases finales. Mide la probabilidad de que 
            un pase derive en gol.
            
            **Goles/90 y Asist/90**  
            Promedios cada 90 minutos (equivalente a un partido completo). Permite comparar jugadores 
            con diferentes minutajes.
            
            **Pases Progresivos**  
            Pases que avanzan significativamente hacia el arco rival. Se considera progresivo si 
            acerca el balón al menos 10 metros hacia la meta contraria.
            """)
        
        with col2:
            st.markdown("""
            **Key Passes**  
            Pases que generan directamente una oportunidad de gol. No necesariamente terminan en 
            asistencia, pero crean situaciones claras.
            
            **Dribbles exitosos**  
            Regates completados superando a un rival con el balón controlado.
            
            **Shot Creating Actions**  
            Acciones ofensivas que llevan directamente a un tiro. Incluye pases, dribbles, faltas 
            recibidas, entre otras.
            """)
        
        st.markdown("""
        ---
        ### Métricas Defensivas
        """)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("""
            **Recoveries (Recuperaciones)**  
            Veces que un jugador recupera la pelota cuando no había nadie del equipo rival en 
            posesión clara.
            
            **Tackles**  
            Entradas o barridas exitosas donde se recupera el balón o se interrumpe un avance rival.
            
            **Interceptions**  
            Anticipaciones donde el jugador intercepta un pase rival.
            """)
        
        with col4:
            st.markdown("""
            **Aerial Won (Duelos Aéreos Ganados)**  
            Duelos por balones aéreos ganados. Relevante para defensores centrales 
            y delanteros.
            
            **Blocks**  
            Bloqueos de tiros rivales con el cuerpo.
            
            **Clearances**  
            Despejes defensivos, usualmente bajo presión.
            """)
        
        st.markdown("""
        ---
        ### Métricas Generales
        """)
        
        st.markdown("""
        **Rating (Nota Promedio)**  
        Calificación general del rendimiento en escala 0-10. Considera múltiples factores: 
        goles, asistencias, pases, duelos, errores, etc. Ponderado por minutos jugados.
        
        **Percentiles**  
        Indican la posición del jugador respecto a otros de su misma posición.  
        - Percentil 90 = mejor que el 90% de jugadores en esa estadística
        - Percentil 50 = mediano, ni bueno ni malo
        - Percentil 10 = solo mejor que el 10%, bastante por debajo del promedio
        
        Los percentiles se calculan DENTRO de cada posición y temporada, para comparar 
        solo jugadores en contextos similares.
        
        **Minutos jugados**  
        Total de minutos en cancha. El sistema filtra jugadores con menos de 300 minutos 
        por temporada (equivalente a ~3-4 partidos completos) para evitar datos estadísticamente 
        poco confiables.
        """)
    
    else:  # English
        st.header("📊 Metrics Glossary")
        
        st.markdown("""
        ---
        ### Offensive Metrics
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **xG (Expected Goals)**  
            Expected goals based on the quality of chances generated. An xG of 0.8 means that, 
            on average, that chance results in a goal 80% of the time.
            
            **xA (Expected Assists)**  
            Expected assists based on the quality of final passes. Measures the probability that 
            a pass leads to a goal.
            
            **Goals/90 and Assists/90**  
            Averages per 90 minutes (equivalent to a full match). Allows comparing players 
            with different minutes played.
            
            **Progressive Passes**  
            Passes that significantly advance toward the opponent's goal. Considered progressive if 
            it brings the ball at least 10 meters closer to the opposing goal.
            """)
        
        with col2:
            st.markdown("""
            **Key Passes**  
            Passes that directly generate a goal opportunity. Don't necessarily result in 
            assists, but create clear situations.
            
            **Successful Dribbles**  
            Completed dribbles beating an opponent with controlled ball.
            
            **Shot Creating Actions**  
            Offensive actions that directly lead to a shot. Includes passes, dribbles, fouls 
            drawn, among others.
            """)
        
        st.markdown("""
        ---
        ### Defensive Metrics
        """)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("""
            **Recoveries**  
            Times a player recovers the ball when no opposing team player had 
            clear possession.
            
            **Tackles**  
            Successful tackles where the ball is recovered or an opponent's advance is stopped.
            
            **Interceptions**  
            Anticipations where the player intercepts an opponent's pass.
            """)
        
        with col4:
            st.markdown("""
            **Aerial Won (Aerial Duels Won)**  
            Aerial duels won. Relevant for center backs 
            and forwards.
            
            **Blocks**  
            Blocked opponent shots with the body.
            
            **Clearances**  
            Defensive clearances, usually under pressure.
            """)
        
        st.markdown("""
        ---
        ### General Metrics
        """)
        
        st.markdown("""
        **Rating (Average Rating)**  
        Overall performance rating on a 0-10 scale. Considers multiple factors: 
        goals, assists, passes, duels, errors, etc. Weighted by minutes played.
        
        **Percentiles**  
        Indicate the player's position relative to others in their same position.  
        - 90th percentile = better than 90% of players in that statistic
        - 50th percentile = median, neither good nor bad
        - 10th percentile = only better than 10%, well below average
        
        Percentiles are calculated WITHIN each position and season, to compare 
        only players in similar contexts.
        
        **Minutes Played**  
        Total minutes on the field. The system filters players with less than 300 minutes 
        per season (equivalent to ~3-4 full matches) to avoid statistically 
        unreliable data.
        """)

# ==================== TAB 2: CONCEPTOS TÉCNICOS ====================
with tab_tecnico:
    if lang == 'es':
        st.header("🔧 Conceptos Técnicos del Sistema")
        
        st.markdown("""
        ---
        ### Arquitectura General
        """)
        
        col_tech1, col_tech2 = st.columns([2, 1])
        
        with col_tech1:
            st.markdown("""
            El sistema está construido sobre tres pilares:
            
            1. **Base de datos** (Google BigQuery)  
               Almacena datos históricos de múltiples temporadas con métricas estandarizadas.
            
            2. **Búsqueda y procesamiento** (Python)  
               Algoritmos de búsqueda fuzzy, normalización de texto y cálculos estadísticos.
            
            3. **Interfaz web** (Streamlit)  
               Aplicación interactiva para visualizar y explorar los datos.
            """)
        
        with col_tech2:
            st.info("""
            **Stack técnico:**
            - Python 3.10+
            - Streamlit
            - BigQuery
            - Pandas
            - Plotly
            - Scikit-learn
            """)
        
        st.markdown("""
        ---
        ### K-Nearest Neighbors (K-NN)
        
        El algoritmo K-NN es un método de clasificación y regresión que identifica elementos 
        similares basándose en distancia en un espacio multidimensional.
        
        **¿Cómo funciona en este sistema?**
        
        1. **Representación vectorial**: Cada jugador es un punto en un espacio de 7+ dimensiones
        2. **Distancia entre jugadores**: Se calcula la distancia euclidiana entre vectores
        3. **Ponderación por posición**: Mayor peso en métricas relevantes por posición
        4. **Decay temporal**: Datos más recientes tienen mayor peso
        5. **Normalización por percentiles**: Comparación justa dentro de cada posición
        
        ---
        ### Principal Component Analysis (PCA)
        
        PCA es una técnica de reducción dimensional que proyecta datos de alta dimensión 
        en un espacio visualizable de 2 dimensiones.
        
        **Interpretación del mapa:**
        - Jugadores cercanos = perfiles similares
        - PC1 y PC2 explican ~70-80% de la varianza
        - Permite identificar clusters de estilos de juego
        """)
    
    else:  # English
        st.header("🔧 System Technical Concepts")
        
        st.markdown("""
        ---
        ### General Architecture
        """)
        
        col_tech1, col_tech2 = st.columns([2, 1])
        
        with col_tech1:
            st.markdown("""
            The system is built on three pillars:
            
            1. **Database** (Google BigQuery)  
               Stores historical data from multiple seasons with standardized metrics.
            
            2. **Search and processing** (Python)  
               Fuzzy search algorithms, text normalization, and statistical calculations.
            
            3. **Web interface** (Streamlit)  
               Interactive application to visualize and explore data.
            """)
        
        with col_tech2:
            st.info("""
            **Tech stack:**
            - Python 3.10+
            - Streamlit
            - BigQuery
            - Pandas
            - Plotly
            - Scikit-learn
            """)
        
        st.markdown("""
        ---
        ### K-Nearest Neighbors (K-NN)
        
        The K-NN algorithm is a classification and regression method that identifies similar 
        elements based on distance in multidimensional space.
        
        **How does it work in this system?**
        
        1. **Vector representation**: Each player is a point in 7+ dimensional space
        2. **Distance between players**: Euclidean distance is calculated between vectors
        3. **Position weighting**: Higher weight on relevant metrics per position
        4. **Temporal decay**: More recent data has higher weight
        5. **Percentile normalization**: Fair comparison within each position
        
        ---
        ### Principal Component Analysis (PCA)
        
        PCA is a dimensional reduction technique that projects high-dimensional data 
        into a visualizable 2-dimensional space.
        
        **Map interpretation:**
        - Close players = similar profiles
        - PC1 and PC2 explain ~70-80% of variance
        - Allows identifying playing style clusters
        """)

# ==================== TAB 3: DISCLAIMERS ====================
with tab_disclaimers:
    if lang == 'es':
        st.header("⚠️ Limitaciones y Uso Responsable")
        
        st.warning("""
        Este sistema analiza el **rendimiento estadístico** de jugadores basándose en datos 
        objetivos de partidos. Sin embargo, es importante entender sus alcances y limitaciones.
        """)
        
        st.markdown("""
        ### Qué NO capturan las estadísticas:
        """)
        
        col_limit1, col_limit2 = st.columns(2)
        
        with col_limit1:
            st.markdown("""
            **Aspectos tácticos:**
            - Inteligencia táctica
            - Posicionamiento sin pelota
            - Comunicación y liderazgo
            - Adaptación táctica
            
            **Aspectos físicos:**
            - Estado físico real
            - Historial de lesiones
            - Resistencia a la fatiga
            """)
        
        with col_limit2:
            st.markdown("""
            **Aspectos contextuales:**
            - Nivel de la competición
            - Calidad de compañeros
            - Sistema de juego del equipo
            - Momento emocional
            
            **Aspectos intangibles:**
            - Mentalidad competitiva
            - Profesionalismo
            - Liderazgo
            """)
        
        st.markdown("""
        ---
        ### Filosofía de Uso: Filtro Inicial, No Veredicto Final
        """)
        
        st.info("""
        **Este sistema es una PRIMERA APROXIMACIÓN, no un veredicto final.**
        
        Las estadísticas son un mapa: te muestran el terreno, pero no caminan en tu lugar.
        """)
        
        st.success("""
        **El sistema es útil para:**
        - Reducir el universo de opciones
        - Encontrar patrones objetivos
        - Validar intuiciones con datos
        - Descubrir jugadores en mercados menos visibles
        """)
        
        st.error("""
        **El sistema NO debe usarse para:**
        - Tomar decisiones sin validación adicional
        - Reemplazar el análisis visual
        - Ignorar el contexto táctico
        - Evaluar jugadores con pocos minutos
        """)
    
    else:  # English
        st.header("⚠️ Limitations and Responsible Use")
        
        st.warning("""
        This system analyzes players' **statistical performance** based on objective 
        match data. However, it's important to understand its scope and limitations.
        """)
        
        st.markdown("""
        ### What statistics DON'T capture:
        """)
        
        col_limit1, col_limit2 = st.columns(2)
        
        with col_limit1:
            st.markdown("""
            **Tactical aspects:**
            - Tactical intelligence
            - Off-ball positioning
            - Communication and leadership
            - Tactical adaptation
            
            **Physical aspects:**
            - Real physical condition
            - Injury history
            - Fatigue resistance
            """)
        
        with col_limit2:
            st.markdown("""
            **Contextual aspects:**
            - Competition level
            - Teammates' quality
            - Team's playing system
            - Emotional state
            
            **Intangible aspects:**
            - Competitive mentality
            - Professionalism
            - Leadership
            """)
        
        st.markdown("""
        ---
        ### Usage Philosophy: Initial Filter, Not Final Verdict
        """)
        
        st.info("""
        **This system is a FIRST APPROACH, not a final verdict.**
        
        Statistics are a map: they show you the terrain, but don't walk for you.
        """)
        
        st.success("""
        **The system is useful for:**
        - Reducing the universe of options
        - Finding objective patterns
        - Validating intuitions with data
        - Discovering players in less visible markets
        """)
        
        st.error("""
        **The system should NOT be used to:**
        - Make decisions without additional validation
        - Replace visual analysis
        - Ignore tactical context
        - Evaluate players with few minutes
        """)

logger.info(f"Glossary page rendered (lang: {lang})")