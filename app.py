import altair as alt
import streamlit as st
import pandas as pd
import os 
import io
import plotly.graph_objects as go

# Set up our App
st.set_page_config(page_title = "Analisador de Dados .CSV", layout='wide')
st.title("Analisador de Dados .CSV")
st.write("Transforma os dados .CSV  em informações na forma de graficos e tabelas exportáveis")

uploaded_file = st.file_uploader("Escolha um arquivo .CSV", type="csv", accept_multiple_files=False)

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[-1].lower()
    if file_ext == '.csv':
        st.success("Arquivo carregado com sucesso!")
        df = pd.read_csv(uploaded_file, sep=';' ,encoding='utf-8')
    elif file_ext != '.csv':
        st.warning(f"Extensão{file_ext} não suportada")
    else: 
        pass

    # Display file information
    st.write(f"**Nome do arquivo:** {uploaded_file.name}")
    st.write(f"**Tamanho do arquivo:** {int(uploaded_file.size/1024)} kbytes")

    # Show 5 rows of dataframe
    st.write("Preview do Arquivo:")
    st.dataframe(df.head())

   

    # Choose category column to create pareto chart - up to 3 colunms can be choosed at once)
    st.subheader(f"Escolha coluna 'Categoria' no arquivo '{uploaded_file.name}' para criar o Gráfico de Pareto:")
    columns = st.multiselect("Selecione as colunas:", df.columns, default=df.columns[3:8]) 
        
    if st.button("Criar Gráficos de Pareto"):
        if len(columns) == 0:
            st.warning("Nenhuma coluna selecionada!")
        else:
            # Converting time columns to timedelta to allow calculations
            df['duration'] = pd.to_timedelta(df['duration'])
            df['start'] = pd.to_datetime(df['start'])
            df['end'] = pd.to_datetime(df['end'])

            # Transforma a coluna 'duration' em decimal e calcula o tempo total de downtime
            df['duration'] = df['duration'].dt.total_seconds() / 3600 # Transforma a coluna duration em decimal de horas
            downtime_hrs = df['duration'].sum()

             # Calcular o intervalo de tempo do periodo
            ts_inicio = df['start'].iloc[-1] # Pega o primeiro timestamp do dataframe
            ts_ini_dia = ts_inicio.normalize() # Normaliza o timestamp para o inicio do dia

            ts_fim = df['start'].iloc[0] # Pega o ultimo timestamp do dataframe
            ts_fim_dia = (ts_fim.normalize()) + pd.Timedelta(hours=24) # Normaliza o timestamp para o inicio do dia e soma 24 horas

            ts_delta = ts_fim_dia - ts_ini_dia # Calcula o intervalo entre os dois timestamps (= periodo total)
            ts_delta_hrs = ts_delta.total_seconds() / 3600 # Transforma o intervalo em decimal de horas

            # Calculate Downtime %
            downtime_perc = (downtime_hrs / ts_delta_hrs) * 100
            
            # Concatenate selected columns into a new column
            df['coluna_concatenada'] = df[columns].agg('-'.join, axis=1)

            # Group by the concatenated column and sum the durations
            pareto_df = df.groupby('coluna_concatenada')['duration'].sum().sort_values(ascending=False).reset_index()

            # Calculate cumulative percentage
            # pareto_df['Percentual Acumulado'] = pareto_df['duration'].cumsum() / pareto_df['duration'].sum() * 100

            # Altair chart with labels
            chart = alt.Chart(pareto_df).mark_bar().encode(
                x=alt.X('coluna_concatenada:N', sort='-y', title='Categoria'),
                y=alt.Y('duration:Q', title='Duração'),
                tooltip=['coluna_concatenada', 'duration']
            ).properties(
                width='container',
                height=500
            ) + alt.Chart(pareto_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-5, # Moves the label up a bit
                color='white'  
            ).encode(
                x='coluna_concatenada:N',
                y='duration:Q',
                text=alt.Text('duration:Q', format='.2f')  # Adjust format if needed
            )

            # Show key information (total downtime, total downtime percentage, and total period)
            st.markdown(f"Período Total hrs: <span style='color:yellow'>{ts_delta_hrs:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"Total de Downtime hrs: <span style='color:yellow'>{downtime_hrs:.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"Total de Downtime %: <span style='color:yellow'>{downtime_perc:.2f}</span>", unsafe_allow_html=True)

            st.altair_chart(chart, use_container_width=True)

            #---------------------------------------------------------
            # GRAFICO DE PARETO
                    
            df = pd.DataFrame(pareto_df)

            # Ordenar por frequência em ordem decrescente
            df = df.sort_values(by='duration', ascending=False).reset_index(drop=True)

            # Calcular frequência acumulada e porcentagem acumulada
            df['Frequência Acumulada'] = df['duration'].cumsum()
            df['Porcentagem Acumulada'] = (df['Frequência Acumulada'] / df['duration'].sum() * 100).round(2)

            # Criar o gráfico de Pareto com Plotly
            fig = go.Figure()

            # Adicionar barras para as frequências
            fig.add_trace(go.Bar(x=df['coluna_concatenada'], y=df['duration'], name='Frequência'))

            # Adicionar linha para a porcentagem acumulada
            fig.add_trace(go.Scatter(x=df['coluna_concatenada'], y=df['Porcentagem Acumulada'],
                                    mode='lines+markers', name='Porcentagem Acumulada', yaxis='y2',
                                    text=df['Porcentagem Acumulada'].astype(str) + '%', textposition='top center'))

            # Atualizar o layout para incluir o segundo eixo Y
            fig.update_layout(
                yaxis=dict(title='Frequência'),
                yaxis2=dict(title='Porcentagem Acumulada', overlaying='y', side='right'),
                title='Gráfico de Pareto',
                height=700,
            )

            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig) 

            df = df.iloc[:, 0:4]
            st.dataframe(df, use_container_width=True)


            # Converter o DataFrame para bytes no formato Excel
            output = io.BytesIO()
            df.to_excel(output, index=False, sheet_name='Dados')
            excel_data = output.getvalue()

            # Oferecer o botão de download
            st.download_button(
                label="Baixar DataFrame como Excel", 
                data=excel_data, file_name="dataframe.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )     
              
