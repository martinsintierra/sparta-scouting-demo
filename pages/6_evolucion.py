import streamlit as st
from utils.logger import setup_logger

logger = setup_logger(__name__)

st.set_page_config(page_title="Glosario y Conceptos", layout="wide", page_icon="📖")

st.title("📖 Glosario y Contexto Técnico")
st.markdown("Guía de interpretación, conceptos técnicos y limitaciones del sistema.")

# Tabs principales
tab_glosario, tab_tecnico, tab_disclaimers = st.tabs([
    "📚 Glosario de Métricas", 
    "🔧 Conceptos Técnicos", 
    "⚠️ Limitaciones y Uso Responsable"
])

# ==================== TAB 1: GLOSARIO ====================
with tab_glosario:
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
        Veces que un jugador recupera el balón cuando no había nadie del equipo rival en 
        posesión clara.
        
        **Tackles**  
        Entradas o barridas exitosas donde se recupera el balón o se interrumpe un avance rival.
        
        **Interceptions**  
        Anticipaciones donde el jugador intercepta un pase rival.
        """)
    
    with col4:
        st.markdown("""
        **Aerial Won (Duelos Aéreos Ganados)**  
        Duelos por balones aéreos ganados. Especialmente relevante para defensores centrales 
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

# ==================== TAB 2: CONCEPTOS TÉCNICOS ====================
with tab_tecnico:
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
    - Intuitivo: "muéstrame quién se parece a este jugador"
    
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
    - No entiende contexto semántico ("Kun" no encuentra "Agüero" automáticamente)
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

# ==================== TAB 3: DISCLAIMERS ====================
with tab_disclaimers:
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
        - Posicionamiento sin balón
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
        - Influencia del entrenador
        - Adaptabilidad a nuevos entornos o ligas
        
        **Aspectos intangibles:**
        - Mentalidad y carácter competitivo
        - Profesionalismo y disciplina
        - Capacidad de liderazgo
        - Ambición y hambre de triunfo
        """)
    
    st.markdown("""
    ---
    ### Filosofía de Uso: Filtro Inicial, No Veredicto Final
    """)
    
    st.info("""
    **Este sistema es una PRIMERA APROXIMACIÓN, no un veredicto final.**
    
    Las estadísticas son como un mapa: te muestran el terreno, pero no caminan en tu lugar.
    """)
    
    st.markdown("""
    **Uso correcto del sistema:**
    
    1. **Filtro inicial**  
       Identifica jugadores con perfiles estadísticos similares al que buscas.
    
    2. **Generación de hipótesis**  
       Descubre opciones que quizás no habías considerado (ligas menores, mercados menos visibles).
    
    3. **Punto de partida**  
       Las estadísticas te dicen "dónde mirar", no "a quién fichar".
    
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
        
        "Este delantero de 24 años tiene xG alto y valor bajo. Es una ganga, hay que ficharlo ya."
        
        *Problema: decisión basada solo en números, sin contexto ni validación.*
        """)
    
    with col_ej2:
        st.success("""
        **Interpretación CORRECTA:**
        
        "Este perfil estadístico es interesante. Valdría la pena:
        - Ver 3-4 partidos completos
        - Investigar por qué su valor es bajo (lesiones, problemas de conducta, liga menor)
        - Evaluar si su estilo encaja con nuestro sistema
        - Confirmar con scouts locales si el dato es real o hay contexto que explique los números"
        
        *Enfoque: estadísticas como punto de partida, no como decisión final.*
        """)
    
    st.markdown("""
    ---
    ### Combinación Óptima: Datos + Observación + Contexto
    """)
    
    col_peso1, col_peso2, col_peso3 = st.columns(3)
    
    with col_peso1:
        st.metric("📊 Datos estadísticos", "30%", help="Lo que se ve en este sistema")
    
    with col_peso2:
        st.metric("👁️ Observación directa", "40%", help="Ver jugar al jugador en vivo o en video")
    
    with col_peso3:
        st.metric("🧠 Contexto e intuición", "30%", help="Experiencia humana, conversaciones, contexto")
    
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
    
    Este sistema te ayuda a trabajar de forma más eficiente, pero nunca reemplaza el ojo 
    experto, la conversación humana y el análisis de contexto.
    
    Usa los datos como aliados, no como dictadores de decisiones.
    """)

logger.info("Glosario page rendered")