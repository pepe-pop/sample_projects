
# Load R packages
install.packages("shinythemes")

library(shiny)
library(shinythemes)

library(dplyr)
library(ggplot2)
library(tidyverse)


data <-read.csv("data.csv", header = TRUE, sep=",")

dane <- data%>%filter(rok %in% c(2006,2007,2008))%>%unite(year_month,c(rok,miesiac),sep="-",remove=FALSE)%>%mutate(pora_roku = ifelse(miesiac %in% c(1,2,12),"zima",ifelse(miesiac %in% c(3,4,5),"wiosna",ifelse(miesiac %in% c(6,7,8),"lato","jesien"))))
dane$year_month <- strptime(paste(as.character(dane$year_month),"-01"),format="%Y-%m -%d")

dane$year_month <- as.Date(dane$year_month)
dane$pora_roku <- as.factor(dane$pora_roku)

variable_options <-
  c(
    "SOR",
    "Kardiologia/Kardiochirurgia",
    "Neurologia",
    "Chirurgia",
    "Gastrologia",
    "Nefrologia",
    "Temperatura powietrza",
    "Ci�nienie atmosferyczne",
    "temperatura rosy",
    "skumulowane opady",
    "Wilgotno�� w %"
  )


# Define UI
ui <- fluidPage(theme = shinytheme("cosmo"),
                navbarPage(
                  
                  "Wizualizacja zbioru dot. wp�ywu pogody na przyj�cia w szpitalu",
                  tabPanel("Podstawowe dane",
                           sidebarPanel(
                             selectInput("summary","Podsumowanie zmiennej: ",
                                         choices = variable_options
                                         )
                           ),
                           mainPanel(
                             verbatimTextOutput("summaryzrzut"),
                             plotOutput("boxplot")
                           
                           )
                          )
                        ,
                  
                  
              
                  tabPanel("Czynniki pogodowe",
                           sidebarPanel(
                             selectInput("weather","Rodzaj badanego czynnika pogodowego: ",
                                         choices = c("Temperatura powietrza",
                                                        "Ci�nienie atmosferyczne",
                                                        "temperatura rosy",
                                                        "skumulowane opady",
                                                        "Wilgotno�� w %"))),
                             
                            
                           mainPanel(
                             plotOutput("warunkiplot")
                           ) 
                           
                  ), 
                  tabPanel("Przyj�cia na oddzia� na przestrzeni lat",
                           sidebarPanel(
                             selectInput(inputId = "oddzial",
                                         label = "Rodzaj oddzia�u:",
                                         choices = c(
                                           "SOR",
                                           "Kardiologia/Kardiochirurgia",
                                           "Neurologia",
                                           "Chirurgia",
                                           "Gastrologia",
                                           "Nefrologia")
                                         )
                             
                           ),
                           mainPanel(
                             plotOutput(outputId = "oddzialplot")
                           )),
                  tabPanel("Zale�no�� ilo�ci chorych od warunk�w pogodowych",
                           sidebarPanel(
                             selectInput("pogoda", "Rodzaj warunku pogodowego: ",
                                         choices = c("Temperatura powietrza",
                                         "Ci�nienie atmosferyczne",
                                         "temperatura rosy",
                                         "skumulowane opady",
                                         "Wilgotno�� w %")
                           ),
                           selectInput("choroba", "Rodzaj oddzia�u: ",
                                       choices = c("SOR",
                                                   "Kardiologia/Kardiochirurgia",
                                                   "Neurologia",
                                                   "Chirurgia",
                                                   "Gastrologia",
                                                   "Nefrologia"))
                           
                           
                           
                           ),
                           
                      mainPanel(plotOutput("final"))
                  
                ),
                tabPanel("Model predykcyjny",
                         sidebarPanel(
                           selectInput("sekcja","Rodzaj oddzia�u: ",
                                       choices = c("SOR",
                                                   "Kardiologia/Kardiochirurgia",
                                                   "Neurologia",
                                                   "Chirurgia",
                                                   "Gastrologia",
                                                   "Nefrologia")),
                           sliderInput("deszcz","Skumulowany opad",min=round(min(dane$opad),0),max=round(max(dane$opad),0),value=622),
                           sliderInput("temp","Temperatura powietrza",min=round(min(dane$temp_pow),0),max=round(max(dane$temp_pow),0),value=9.3),
                           sliderInput("rosa","Temperatura rosy",min=round(min(dane$temp_rosy),0),max=round(max(dane$temp_rosy),0),value=2.6),
                           sliderInput("wilgotnosc","Wilgotno��",min=round(min(dane$wilgotnosc),0),max=round(max(dane$wilgotnosc),0),value=58.5),
                           sliderInput("cisnienie","Ci�nienie",min=round(min(dane$cisnienie),0),max=round(max(dane$cisnienie),0),value=980),

                           actionButton("submitbutton", "Submit", class = "btn btn-primary")
                         ),
                         mainPanel(
                           tags$label(h3('Status/Output')), # Status/Output Text Box
                           verbatimTextOutput('contents'),
                           tableOutput('tabledata'),
                           #verbatimTextOutput("printmodel") # Prediction results table
                         )
                )   
                )# navbarPage
) # fluidPage


# Define server function  
server <- function(input, output) {
  data_summary <- reactive({
    if ( "Temperatura powietrza" %in% input$summary) return(dane$temp_pow)
    if ( "Ci�nienie atmosferyczne" %in% input$summary) return(dane$cisnienie)
    if ( "temperatura rosy" %in% input$summary) return(dane$temp_rosy)
    if ( "skumulowane opady" %in% input$summary) return(dane$opad)
    if ( "Wilgotno�� w %" %in% input$summary) return(dane$wilgotnosc)
    if ( "SOR" %in% input$summary) return(dane$SOR)
    if ( "Kardiologia/Kardiochirurgia" %in% input$summary) return(dane$Kardiologia.Kardiochirurgia)
    if ( "Neurologia" %in% input$summary) return(dane$Neurologia)
    if ( "Chirurgia" %in% input$summary) return(dane$Chirurgia)
    if ( "Gastrologia" %in% input$summary) return(dane$Gastrologia)
    if ( "Nefrologia" %in% input$summary) return(dane$Nefrologia)
  })
  
  output$summaryzrzut <- renderPrint({
    summary(data_summary())
  })
  
  output$boxplot <- renderPlot({
    ggplot(dane) + geom_boxplot(aes(as.factor(rok),data_summary())) + xlab("rok") + ylab("warto�� zmiennej")+
      ggtitle("Wykres pude�kowy zmiennej w zalezno�ci od roku") + theme_classic()
    
  })
  
  
  data_0 <- reactive({
    if ( "Temperatura powietrza" %in% input$weather) return(dane$temp_pow)
    if ( "Ci�nienie atmosferyczne" %in% input$weather) return(dane$cisnienie)
    if ( "temperatura rosy" %in% input$weather) return(dane$temp_rosy)
    if ( "skumulowane opady" %in% input$weather) return(dane$opad)
    if ( "Wilgotno�� w %" %in% input$weather) return(dane$wilgotnosc)
  })
  
  
  output$warunkiplot <- renderPlot({
    ggplot(dane,aes(as.factor(miesiac),data_0(),color=as.factor(rok))) + geom_point(size=3) +xlab("miesi�c")+
      ylab("warto�� zmiennej")+ggtitle("Warto�� zmiennej w zale�no�ci od miesi�ca i roku")+labs(color="Rok")+theme_minimal()
  })
  
  data_1 <- reactive({
    if ( "SOR" %in% input$oddzial) return(dane$SOR)
    if ( "Kardiologia/Kardiochirurgia" %in% input$oddzial) return(dane$Kardiologia.Kardiochirurgia)
    if ( "Neurologia" %in% input$oddzial) return(dane$Neurologia)
    if ( "Chirurgia" %in% input$oddzial) return(dane$Chirurgia)
    if ( "Gastrologia" %in% input$oddzial) return(dane$Gastrologia)
    if ( "Nefrologia" %in% input$oddzial) return(dane$Nefrologia)
  })
  
  output$oddzialplot <- renderPlot({
    ggplot(dane) + geom_bar(aes(as.factor(rok),data_1()),stat = "identity",fill="brown3")+xlab("rok")+
      ylab("liczba przypadk�w")+ggtitle("ilo�� pacjent�w przyj�tych na oddzia� na przestrzeni lat")+theme_classic()
  })
  
  data_final <- reactive({
    if ( "Temperatura powietrza" %in% input$pogoda) return(dane$temp_pow)
    if ( "Ci�nienie atmosferyczne" %in% input$pogoda) return(dane$cisnienie)
    if ( "temperatura rosy" %in% input$pogoda) return(dane$temp_rosy)
    if ( "skumulowane opady" %in% input$pogoda) return(dane$opad)
    if ( "Wilgotno�� w %" %in% input$pogoda) return(dane$wilgotnosc)
  })
  
  data_final_2 <- reactive({
    
    if ( "SOR" %in% input$choroba) return(dane$SOR)
    if ( "Kardiologia/Kardiochirurgia" %in% input$choroba) return(dane$Kardiologia.Kardiochirurgia)
    if ( "Neurologia" %in% input$choroba) return(dane$Neurologia)
    if ( "Chirurgia" %in% input$choroba) return(dane$Chirurgia)
    if ( "Gastrologia" %in% input$choroba) return(dane$Gastrologia)
    if ( "Nefrologia" %in% input$choroba) return(dane$Nefrologia)
  })
  
  output$final <- renderPlot({
    
    ggplot(dane)+geom_smooth(aes(x=data_final(),y=data_final_2()),method="lm")+geom_point(aes(x=data_final(),y=data_final_2(),fill=as.factor(rok)),pch=21,size=5)+facet_wrap(~pora_roku)+
      
      xlab("warto�� warunku pogodowego")+ylab("ilo�� os�b, przyj�tych na oddzia�")+
      ggtitle("Wykres zale�no�ci ilo�ci przyj�tych pacjent�w od warto�ci warunku pogodowego, w podziale na pory roku")+
      theme_linedraw()+labs(fill="Rok")
    
    
  })
 
  

  data_final_3 <- reactive({

    if ( "SOR" %in% input$sekcja) return(dane$SOR)
    if ( "Kardiologia/Kardiochirurgia" %in% input$sekcja) return(dane$Kardiologia.Kardiochirurgia)
    if ( "Neurologia" %in% input$sekcja) return(dane$Neurologia)
    if ( "Chirurgia" %in% input$sekcja) return(dane$Chirurgia)
    if ( "Gastrologia" %in% input$sekcja) return(dane$Gastrologia)
    if ( "Nefrologia" %in% input$sekcja) return(dane$Nefrologia)
  })

  datasetInput <- reactive({

    model <- lm(data_final_3()~wilgotnosc+opad+cisnienie+temp_pow+temp_rosy,data=dane)

    df <- data.frame(
      wilgotnosc = input$wilgotnosc,
      opad = input$deszcz,
      cisnienie = input$cisnienie,
      temp_pow = input$temp,
      temp_rosy = input$rosa
      )

    Output <- data.frame(Prediction=round(predict(model,df),0))
    colnames(Output) <- c("Przewidywana liczba pacjent�w w ci�gu miesi�ca na oddziale")
    print(Output)

  })


  output$contents <- renderPrint({
    if (input$submitbutton>0) {
      isolate("Calculation complete.")
    } else {
      return("Server is ready for calculation.")
    }
  })

  output$tabledata <- renderTable({
    if (input$submitbutton>0) {
      isolate(datasetInput())
    }
  })
  

  data_model <-reactive({
    model <- lm(data_final_3()~wilgotnosc+opad+cisnienie+temp_pow+temp_rosy,data=dane)
    podsumowanie <- summary(model)
    print(podsumowanie)
  })
    
  output$printmodel <-renderPrint({
    if (input$submitbutton>0) {
      isolate(data_model())
    }
  })
} # server



# Create Shiny object
shinyApp(ui = ui, server = server)
