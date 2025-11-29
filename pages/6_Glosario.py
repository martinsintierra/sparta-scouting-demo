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
        """)
        
        st.markdown("""
        El algoritmo K-NN es un método de clasificación y regresión que identifica elementos 
        similares basándose en distancia en un espacio multidimensional.
        
        **¿Cómo funciona en este sistema?**
        
        1. **Representación vectorial**  
           Cada jugador es un punto en un espacio de 7+ dimensiones (una por métrica: xG, xA, 
           pases progresivos, recoveries, etc.)
        
        2. **Distancia entre jugadores**  
           Se calcula la distancia euclidiana entre vectores. Jugadores "cercanos" tienen 
           perfiles estadísticos similares.
        
        3. **Ponderación por posición**  
           No todas las métricas pesan igual:
           - Delanteros: mayor peso en xG, xA, dribbles
           - Mediocampistas: mayor peso en pases progresivos, key passes
           - Defensores: mayor peso en recoveries, duelos aéreos, tackles
        
        4. **Decay temporal**  
           Datos más recientes tienen mayor peso que datos antiguos. Un jugador de 2025 
           se compara principalmente con jugadores de 2024-2025, no de 2021.
        
        5. **Normalización por percentiles**  
           Las métricas se normalizan dentro de cada posición para evitar que delanteros 
           y defensores sean directamente comparables en xG (lo cual no tendría sentido).
        
        **Ventajas del K-NN:**
        - No asume una relación lineal entre variables
        - Robusto a datos atípicos
        - Intuitivo: "mostrame quién se "parece" a este jugador"
        
        **Limitaciones:**
        - Sensible a la escala de las variables (por eso normalizamos)
        - Computacionalmente costoso en datasets muy grandes (mitigado con caché)
        - No explica POR QUÉ dos jugadores son similares, solo QUE lo son
        """)
        
        st.markdown("""
        ---
        ### Principal Component Analysis (PCA)
        """)
        
        st.markdown("""
        PCA es una técnica de reducción dimensional que proyecta datos de alta dimensión 
        (7+ métricas) en un espacio de 2 dimensiones visualizable.
        
        **¿Cómo funciona?**
        
        1. **Estandarización**  
           Todas las métricas se llevan a la misma escala (media 0, desviación estándar 1).
        
        2. **Cálculo de componentes principales**  
           Se identifican las direcciones de máxima varianza en los datos. La primera 
           componente (PC1) explica la mayor varianza, la segunda (PC2) la segunda mayor, etc.
        
        3. **Proyección**  
           Cada jugador se proyecta en el nuevo espacio de 2 dimensiones (PC1, PC2).
        
        **Interpretación del mapa PCA:**
        - Jugadores cercanos físicamente en el mapa tienen perfiles estadísticos similares
        - La distancia entre jugadores es proporcional a su diferencia estadística
        - PC1 y PC2 son combinaciones lineales de las métricas originales
        - Típicamente PC1+PC2 explican 70-80% de la varianza total
        
        **Ejemplo práctico:**
        - PC1 podría representar "productividad ofensiva general" (xG + xA + goles)
        - PC2 podría representar "estilo de juego" (dribbles vs pases progresivos)
        
        **Limitaciones:**
        - Pierde información (solo conserva 70-80% de la varianza)
        - Las componentes no siempre tienen interpretación clara
        - Asume relaciones lineales entre variables
        """)
        
        st.markdown("""
        ---
        ### Búsqueda Fuzzy (Levenshtein Distance)
        """)
        
        st.markdown("""
        La búsqueda fuzzy permite encontrar coincidencias aproximadas tolerando errores de tipeo.
        
        **¿Cómo funciona?**
        
        1. **Normalización**  
           Se eliminan tildes, caracteres especiales y se convierte a mayúsculas.
           - "Julián Álvarez" → "JULIAN ALVAREZ"
        
        2. **Distancia de Levenshtein**  
           Cuenta el número mínimo de operaciones (insertar, borrar, sustituir) necesarias 
           para transformar una cadena en otra.
           - "Mesii" vs "Messi" = 1 operación (sustituir 'i' por 's')
           - "Alvares" vs "Alvarez" = 1 operación (sustituir 's' por 'z')
        
        3. **Partial Ratio Scoring**  
           Además de la distancia exacta, evalúa coincidencias parciales.
           - "Gome" encuentra "Valentin Gomez" (substring matching)
        
        4. **Umbral de tolerancia**  
           El usuario ajusta qué tan estricta es la búsqueda (70-100%). Menor umbral = 
           acepta más diferencias.
        
        **Ventajas:**
        - Tolerante a errores humanos
        - Funciona sin tildes ni caracteres especiales
        - Encuentra variaciones del mismo nombre
        
        **Limitaciones:**
        - Puede dar falsos positivos si el umbral es muy bajo
        - No entiende contexto semántico ("Kun" no encontraría "Agüero" automáticamente)
        """)
        
        st.markdown("""
        ---
        ### Sistema de Caché
        """)
        
        st.markdown("""
        Para optimizar performance, el sistema usa múltiples niveles de caché:
        
        **Caché en disco (24 horas)**  
        - Almacena el índice completo de jugadores en formato Parquet
        - Evita consultas repetidas a BigQuery
        - Se regenera automáticamente cada 24 horas
        
        **Caché en memoria (1 hora)**  
        - Mantiene en RAM resultados de queries específicas
        - Usa el decorador @st.cache_data de Streamlit
        - Se limpia al cambiar parámetros de búsqueda
        
        **Búsquedas locales**  
        - La búsqueda fuzzy se hace en memoria sobre el índice cacheado
        - No requiere conexión a BigQuery
        - Respuestas instantáneas (<100ms)
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
        """)
        
        st.markdown("""
        The K-NN algorithm is a classification and regression method that identifies similar 
        elements based on distance in multidimensional space.
        
        **How does it work in this system?**
        
        1. **Vector representation**  
           Each player is a point in a 7+ dimensional space (one per metric: xG, xA, 
           progressive passes, recoveries, etc.)
        
        2. **Distance between players**  
           Euclidean distance is calculated between vectors. "Close" players have 
           similar statistical profiles.
        
        3. **Position-based weighting**  
           Not all metrics weigh equally:
           - Forwards: higher weight on xG, xA, dribbles
           - Midfielders: higher weight on progressive passes, key passes
           - Defenders: higher weight on recoveries, aerial duels, tackles
        
        4. **Temporal decay**  
           More recent data has higher weight than older data. A 2025 player 
           is compared mainly with 2024-2025 players, not with 2021.
        
        5. **Percentile normalization**  
           Metrics are normalized within each position to avoid forwards 
           and defenders being directly comparable on xG (which wouldn't make sense).
        
        **K-NN Advantages:**
        - Doesn't assume linear relationships between variables
        - Robust to outliers
        - Intuitive: "show me who 'resembles' this player"
        
        **Limitations:**
        - Sensitive to variable scale (that's why we normalize)
        - Computationally expensive on very large datasets (mitigated with cache)
        - Doesn't explain WHY two players are similar, only THAT they are
        """)
        
        st.markdown("""
        ---
        ### Principal Component Analysis (PCA)
        """)
        
        st.markdown("""
        PCA is a dimensional reduction technique that projects high-dimensional data 
        (7+ metrics) into a visualizable 2-dimensional space.
        
        **How does it work?**
        
        1. **Standardization**  
           All metrics are brought to the same scale (mean 0, standard deviation 1).
        
        2. **Principal components calculation**  
           The directions of maximum variance in the data are identified. The first 
           component (PC1) explains the greatest variance, the second (PC2) the second greatest, etc.
        
        3. **Projection**  
           Each player is projected into the new 2-dimensional space (PC1, PC2).
        
        **PCA map interpretation:**
        - Players physically close on the map have similar statistical profiles
        - Distance between players is proportional to their statistical difference
        - PC1 and PC2 are linear combinations of the original metrics
        - Typically PC1+PC2 explain 70-80% of total variance
        
        **Practical example:**
        - PC1 might represent "general offensive productivity" (xG + xA + goals)
        - PC2 might represent "playing style" (dribbles vs progressive passes)
        
        **Limitations:**
        - Loses information (only preserves 70-80% of variance)
        - Components don't always have clear interpretation
        - Assumes linear relationships between variables
        """)
        
        st.markdown("""
        ---
        ### Fuzzy Search (Levenshtein Distance)
        """)
        
        st.markdown("""
        Fuzzy search allows finding approximate matches while tolerating typos.
        
        **How does it work?**
        
        1. **Normalization**  
           Accents and special characters are removed, and text is converted to uppercase.
           - "Julián Álvarez" → "JULIAN ALVAREZ"
        
        2. **Levenshtein Distance**  
           Counts the minimum number of operations (insert, delete, substitute) needed 
           to transform one string into another.
           - "Mesii" vs "Messi" = 1 operation (substitute 'i' with 's')
           - "Alvares" vs "Alvarez" = 1 operation (substitute 's' with 'z')
        
        3. **Partial Ratio Scoring**  
           Besides exact distance, evaluates partial matches.
           - "Gome" finds "Valentin Gomez" (substring matching)
        
        4. **Tolerance threshold**  
           User adjusts how strict the search is (70-100%). Lower threshold = 
           accepts more differences.
        
        **Advantages:**
        - Tolerant to human errors
        - Works without accents or special characters
        - Finds variations of the same name
        
        **Limitations:**
        - Can give false positives if threshold is too low
        - Doesn't understand semantic context ("Kun" wouldn't find "Agüero" automatically)
        """)
        
        st.markdown("""
        ---
        ### Cache System
        """)
        
        st.markdown("""
        To optimize performance, the system uses multiple cache levels:
        
        **Disk cache (24 hours)**  
        - Stores complete player index in Parquet format
        - Avoids repeated BigQuery queries
        - Automatically regenerated every 24 hours
        
        **Memory cache (1 hour)**  
        - Keeps specific query results in RAM
        - Uses Streamlit's @st.cache_data decorator
        - Cleared when search parameters change
        
        **Local searches**  
        - Fuzzy search is done in memory on cached index
        - Doesn't require BigQuery connection
        - Instant responses (<100ms)
        """)

# ==================== TAB 3: DISCLAIMERS ====================
with tab_disclaimers:
    if lang == 'es':
        st.header("⚠️ Limitaciones y Uso Responsable")
        
        st.markdown("""
        ---
        ### Alcances de las Estadísticas
        """)
        
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
            **Aspectos tácticos y cognitivos:**
            - Inteligencia táctica y lectura del juego
            - Posicionamiento sin pelota
            - Comunicación y liderazgo en cancha
            - Capacidad de adaptación táctica
            - Timing y toma de decisiones bajo presión
            
            **Aspectos físicos y médicos:**
            - Estado físico real y forma actual
            - Historial de lesiones y predisposición
            - Resistencia a la fatiga en fase final de temporada
            - Recuperación entre partidos
            """)
        
        with col_limit2:
            st.markdown("""
            **Aspectos contextuales:**
            - Nivel de la competición donde juega
            - Calidad de compañeros que lo rodean
            - Sistema de juego y rol específico del DT
            - Momento emocional y situación personal
            - Influencia del técnico
            - Adaptabilidad a nuevos entornos o ligas
            
            **Aspectos intangibles:**
            - Mentalidad y carácter competitivo
            - Profesionalismo y disciplina
            - Capacidad de liderazgo
            - Ambición
            """)
        
        st.markdown("""
        ---
        ### Filosofía de Uso: Filtro Inicial, No Veredicto Final
        """)
        
        st.info("""
        **Este sistema es una PRIMERA APROXIMACIÓN, no un veredicto final.**
        
        Las estadísticas son una suerte de mapa: te muestran el terreno, pero no caminan en tu lugar.
        """)
        
        st.markdown("""
        **Uso correcto del sistema:**
        
        1. **Filtro inicial**  
           Identifica jugadores con perfiles estadísticos similares al que se busca.
        
        2. **Generación de hipótesis**  
           Descubre opciones que quizás no se habían considerado (ligas menores, mercados menos visibles).
        
        3. **Punto de partida**  
           Las estadísticas te dicen "dónde mirar", no "a quién comprar".
        
        **Después del análisis estadístico, es fundamental:**
        
        - Ver partidos completos del jugador (mínimo 3-4 encuentros)
        - Consultar con scouts que lo hayan visto en vivo
        - Investigar su entorno personal y profesional
        - Revisar historial médico
        - Hablar con personas que lo conocen (entrenadores, compañeros)
        - Evaluar compatibilidad con el sistema de juego del equipo
        """)
        
        st.markdown("""
        ---
        ### Ejemplo Práctico: Interpretación Correcta vs Incorrecta
        """)
        
        col_ej1, col_ej2 = st.columns(2)
        
        with col_ej1:
            st.error("""
            **Interpretación INCORRECTA:**
            
            "Este delantero de 24 años tiene xG alto y valor bajo. Está regalado y hay que agarrarlo ya."
            
            *Problema: decisión basada solo en números, sin contexto ni validación.*
            """)
        
        with col_ej2:
            st.success("""
            **Interpretación CORRECTA:**
            
            "Este perfil estadístico es interesante. Estaría bueno:
            - Ver 3-4 partidos completos
            - Investigar por qué su valor es bajo (lesiones, problemas de conducta, liga menor)
            - Evaluar si su estilo encaja con sistema X
            - Confirmar con scouts locales si el dato es real o hay contexto que explique los números"
            
            *Enfoque: estadísticas como punto de partida, no como decisión final.*
            """)
        
        st.markdown("""
        ---
        ### Combinación Óptima: Datos + Observación + Contexto
        """)
        
        col_peso1, col_peso2, col_peso3 = st.columns(3)
        
        with col_peso1:
            st.metric("Datos estadísticos", "30%", help="Lo que se ve en este sistema")
        
        with col_peso2:
            st.metric("Observación directa", "40%", help="Ver jugar al jugador en vivo o en video")
        
        with col_peso3:
            st.metric("Contexto e intuición", "30%", help="Experiencia humana, conversaciones, contexto")
        
        st.markdown("""
        Un buen proceso de scouting combina estas tres dimensiones. Ninguna por sí sola es suficiente.
        """)
        
        st.markdown("""
        ---
        ### Casos de Uso Apropiados
        """)
        
        st.success("""
        **El sistema es útil para:**
        - Reducir el universo de opciones en un mercado amplio
        - Encontrar patrones y similitudes objetivas
        - Validar o cuestionar intuiciones con datos
        - Descubrir jugadores en mercados menos visibles
        - Identificar jugadores en progresión o declive
        - Comparar alternativas de forma objetiva
        """)
        
        st.error("""
        **El sistema NO debe usarse para:**
        - Tomar decisiones de fichaje sin validación adicional
        - Reemplazar el análisis visual de partidos
        - Ignorar el contexto táctico y emocional
        - Evaluar jugadores con muy pocos minutos (<300)
        - Comparar directamente ligas de niveles muy distintos
        """)
        
        st.markdown("""
        ---
        ### Nota Final
        """)
        
        st.info("""
        Las herramientas computacionales son cada vez más sofisticadas, pero el fútbol sigue 
        siendo un deporte humano donde el contexto, el momento y los intangibles importan tanto 
        como los números.
        
        Este sistema ayudaría a trabajar de forma más eficiente, pero nunca sería el reemplazo del ojo 
        experto, la conversación entre pares y/o el análisis de contexto.
        
        """)
    
    else:  # English
        st.header("⚠️ Limitations and Responsible Use")
        
        st.markdown("""
        ---
        ### Scope of Statistics
        """)
        
        st.warning("""
        This system analyzes players' **statistical performance** based on objective 
        match data. However, it's important to understand its scope and limitations.
        """)
        
        st.markdown("""
        ### What statistics DO NOT capture:
        """)
        
        col_limit1, col_limit2 = st.columns(2)
        
        with col_limit1:
            st.markdown("""
            **Tactical and cognitive aspects:**
            - Tactical intelligence and game reading
            - Off-ball positioning
            - On-field communication and leadership
            - Tactical adaptability
            - Timing and decision making under pressure
            
            **Physical and medical aspects:**
            - Actual physical condition and current form
            - Injury history and predisposition
            - Fatigue resistance in the final phase of the season
            - Recovery between matches
            """)
        
        with col_limit2:
            st.markdown("""
            **Contextual aspects:**
            - Level of competition where they play
            - Quality of teammates surrounding them
            - Game system and specific role under the coach
            - Emotional moment and personal situation
            - Coach influence
            - Adaptability to new environments or leagues
            
            **Intangible aspects:**
            - Mentality and competitive character
            - Professionalism and discipline
            - Leadership capacity
            - Ambition
            """)
        
        st.markdown("""
        ---
        ### Usage Philosophy: Initial Filter, Not Final Verdict
        """)
        
        st.info("""
        **This system is a FIRST APPROXIMATION, not a final verdict.**
        
        Statistics are a kind of map: they show you the terrain, but they don't walk it for you.
        """)
        
        st.markdown("""
        **Correct use of the system:**
        
        1. **Initial filter**  
           Identifies players with statistical profiles similar to the one sought.
        
        2. **Hypothesis generation**  
           Discovers options that perhaps hadn't been considered (minor leagues, less visible markets).
        
        3. **Starting point**  
           Statistics tell you "where to look", not "who to buy".
        
        **After statistical analysis, it is fundamental to:**
        
        - Watch full matches of the player (minimum 3-4 games)
        - Consult with scouts who have seen them live
        - Investigate their personal and professional environment
        - Review medical history
        - Talk to people who know them (coaches, teammates)
        - Evaluate compatibility with the team's game system
        """)
        
        st.markdown("""
        ---
        ### Practical Example: Correct vs Incorrect Interpretation
        """)
        
        col_ej1, col_ej2 = st.columns(2)
        
        with col_ej1:
            st.error("""
            **INCORRECT Interpretation:**
            
            "This 24-year-old forward has high xG and low value. He's a steal and must be signed now."
            
            *Problem: decision based only on numbers, without context or validation.*
            """)
        
        with col_ej2:
            st.success("""
            **CORRECT Interpretation:**
            
            "This statistical profile is interesting. It would be good to:
            - Watch 3-4 full matches
            - Investigate why his value is low (injuries, behavioral issues, minor league)
            - Evaluate if his style fits system X
            - Confirm with local scouts if the data is real or if there is context explaining the numbers"
            
            *Approach: statistics as a starting point, not as a final decision.*
            """)
        
        st.markdown("""
        ---
        ### Optimal Combination: Data + Observation + Context
        """)
        
        col_peso1, col_peso2, col_peso3 = st.columns(3)
        
        with col_peso1:
            st.metric("Statistical Data", "30%", help="What is seen in this system")
        
        with col_peso2:
            st.metric("Direct Observation", "40%", help="Watching the player play live or on video")
        
        with col_peso3:
            st.metric("Context & Intuition", "30%", help="Human experience, conversations, context")
        
        st.markdown("""
        A good scouting process combines these three dimensions. None alone is sufficient.
        """)
        
        st.markdown("""
        ---
        ### Appropriate Use Cases
        """)
        
        st.success("""
        **The system is useful for:**
        - Reducing the universe of options in a broad market
        - Finding patterns and objective similarities
        - Validating or questioning intuitions with data
        - Discovering players in less visible markets
        - Identifying players in progression or decline
        - Comparing alternatives objectively
        """)
        
        st.error("""
        **The system should NOT be used to:**
        - Make signing decisions without additional validation
        - Replace visual match analysis
        - Ignore tactical and emotional context
        - Evaluate players with very few minutes (<300)
        - Directly compare leagues of very different levels
        """)
        
        st.markdown("""
        ---
        ### Final Note
        """)
        
        st.info("""
        Computational tools are becoming increasingly sophisticated, but football remains 
        a human sport where context, timing, and intangibles matter as much 
        as the numbers.
        
        This system helps to work more efficiently, but would never replace the expert 
        eye, peer conversation, and/or context analysis.
        """)

logger.info("Glosario page rendered")