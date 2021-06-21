# pakiety - praca w Python 3.8
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
from datetime import datetime,timedelta
import copy
import numpy as np



class Gracz():
    """ klasa definiuje gracza,jako parametry wejściowe należy wpisać nazwę
    oraz początkowy wkład. Klasa ma metody zakup,sprzedaz,stan konta, aktualizacja zakup oraz
    aktualizacja sprzedaz. Dodatkowo aktualizowany kapitał oraz posiadane akcje są magazynowane w
    zmiennej self.wynik"""

    def __init__(self,nazwa,wklad):
        self.nazwa = nazwa
        self.wklad = wklad
        self.wynik = {'kapitał': self.wklad,'akcje':{}}

    def stan_konta(self):
        return print(f"Stan konta wynosi {self.wynik['kapitał']} zł  Posiadane obligacje: {self.wynik['akcje']}")

    def zakup(self):
        papier = str(input("podaj nazwę papieru: ")).upper()
        ilosc = int(input("podaj ilosc akcji: "))
        cena = float(input("podaj oferowaną cenę: "))
        return [self.nazwa,papier,ilosc,cena]
       

    def sprzedaz(self):
        papier = str(input("podaj nazwę papieru: ")).upper()
        ilosc = int(input("podaj ilosc akcji: "))
        cena = float(input("podaj oferowaną cenę: "))
        return [self.nazwa,papier,ilosc,cena]

            
            
    def aktualizacja_zakup(self,zlecenia):
        self.zlecenia = zlecenia
        for gracz in self.zlecenia[self.zlecenia['Gracz']==self.nazwa].values.tolist():
            self.wynik['kapitał'] = self.wynik['kapitał']-gracz[3]*gracz[6]

            if gracz[1] in self.wynik['akcje'].keys():
                self.wynik['akcje'][gracz[1]] = self.wynik['akcje'][gracz[1]]+gracz[6]
            else:
                self.wynik['akcje'][gracz[1]]=gracz[6]

                    
    def aktualizacja_sprzedaz(self,zlecenia):

        self.zlecenia = zlecenia
        for gracz in self.zlecenia[self.zlecenia['Gracz']==self.nazwa].values.tolist():

            self.wynik['akcje'][gracz[1]] = self.wynik['akcje'][gracz[1]]-gracz[2]
            self.wynik['kapitał'] = self.wynik['kapitał']+gracz[3]*gracz[2]


            




class Giełda():
    """ klasa definiuje akcje, które pojawiły się na giełdzie w pożądanym okresie czasu. Dane giełdy
    są pobierane ze strony https://www.gpw.pl/archiwum-notowan-full . Parametrem wejściowym jest data
    konkretnego dnia, aby z niego pobrać dane z giełdy."""

    def __init__(self,data):
        self.data = data
        self.dataframe = self.data_import()
        self.wartosci = self.wynik()
        
    def wynik(self):
        wartosci = self.dataframe[['Nazwa','Kurs maksymalny','Kurs minimalny','Wolumen obrotu (w szt.)']]
        wartosci = wartosci.convert_dtypes()
        wartosci['Kurs maksymalny'] = wartosci.iloc[:,1].str.replace(',','.')
        wartosci['Kurs minimalny'] = wartosci.iloc[:,2].str.replace(',','.')
        wartosci['Kurs maksymalny'] = wartosci.iloc[:,1].str.replace(' ','')
        wartosci['Kurs minimalny'] = wartosci.iloc[:,2].str.replace(' ','')
        wartosci['Wolumen obrotu (w szt.)'] = wartosci.iloc[:,3].str.replace(' ','')
        wartosci[['Kurs maksymalny','Kurs minimalny']]=wartosci[['Kurs maksymalny','Kurs minimalny']].astype('float')
        wartosci['Wolumen obrotu (w szt.)']=wartosci['Wolumen obrotu (w szt.)'].astype('int')
        wartosci.columns = ['Nazwa','max','min','wolumen']
        return wartosci
    
    def data_import(self):
        gpw_url = 'https://www.gpw.pl/archiwum-notowan-full?type=10&instrument=&date='+self.data
        gpw = requests.get(gpw_url)
        gpw_bs = bs(gpw.text, 'html.parser')
        gpw = gpw_bs.find('table',{'class':'table footable'})
        table_rows = gpw.findAll('tr')

        res = []

        for tr in table_rows:
            td = tr.find_all('td')
            th = tr.find_all('th')
            row = [tr.text.strip() for tr in td if tr.text.strip()]
            head = [tr.text.strip() for tr in th if tr.text.strip()]
            if row:
                res.append(row)
            else:
                res.append(head)

        df = pd.DataFrame(res[1:], columns =res[0])
        return df
    

class Gra():
    """ klasa definiująca samą grę. Parametrami wejściowymi jest data rozpoczęcia gry, data zakonczenia gry oraz
    wcześniej zdefiniowani gracze. Klasa posiada jedną metodę - rozpocznij - która zaczyna rozgrywkę. Jeżeli
    między datami rozpoczęcia i zakonczenia znajduje się dzień weekendowy to ten dzień jest pomijany -> specyfika
     samej giełdy, ponieważ giełda wtedy nie działa. Datę należy wpisać w formacie 'dd-mm-yyyy' """

    """ Pierwszym krokiem jest wybór konkretnej akcji przez gracza
            * zakup - gracz wyraża chęć zakupu akcji 
                    - gracz musi wpisac nazwę akcji, ilość papieru oraz cenę
                    - jeżeli nazwa papieru nie będzie tego dnia na giełdzie to pojawi się komunikat
                    - jeżeli oferowana cena będzie wyższa od maksymalnej na giełdzie to pojawi się komunikat
            * sprzedaz - gracz wyraża chęc sprzedaży akcji
                        - gracz musi wpisac jaki papier, w jakiej ilosci oraz w jakiej cenie chce go sprzedać
                        - jeżeli brak papieru w posiadanych to pojawi się komunikat
                        - jeżeli cena oferowana będzie niższa od minimalnej na giełdzie to pojawi sie komunikat
            * stan konta - gracz sprawdza swój stan konta
            * jeżeli gracz zostawi puste pole to brak jakiejkolwiek akcji i następuje kolej kolejnego gracza
        
            
        Akcje są iterowane po wszystkich graczach. Następnie sprawdzane jest czy ilość pożądana przez graczy w jednej
        rundzie jest mniejsza od dostępnej na giełdzie. Jeżeli nie to następuje proporcjonalne dzielenie ilości
        papieru. Następnie następuje pytanie, czy gracze chcą kończyć dzienną rundę i przejść do kolejnego dnia.
        W tym momencie należy wpisać:
            * tak -> jeżeli gracze chcą przejść do kolejnego dnia gry
            * nie -> jeżeli gracze chcą zakupić/sprzedać akcje danego dnia
        
        W momencie, gdy nastąpi ostatni dzień rozgrywki i pojawi się komunikat o chęci rozegrania kolejnego dnia, 
        należy wpisać 'tak'. Wtedy pokaże się podsumowanie czyli komunikat o wkładzie początkowym, 
        kapitale finalnym oraz stosunku kapitału finalnego do kapitału początkowego
        """
    def __init__(self,data_rozpoczecia,data_zakonczenia,*gracze):
        self.poczatek = data_rozpoczecia
        self.koniec = data_zakonczenia
        self.gracze = list(gracze)
        
    def rozpocznij(self):
        start_date = datetime.strptime(self.poczatek,'%d-%m-%Y')
        end_date = datetime.strptime(self.koniec,'%d-%m-%Y')
        delta = timedelta(days=1)

        while True:
            try:
                day = str(start_date)
                data = day[8:10] + '-' + day[5:7] + '-' + day[:4]
                giełda = Giełda(data).wartosci
                break
            except:
                start_date += delta

        while start_date <= end_date:



            try:


                zlecenia_kupno = []
                zlecenia_sprzedaz = []
                print('Data gry: ' + data)
                for gracz in self.gracze:


                    kasa = copy.copy(gracz.wynik['kapitał'])
                    papiery = copy.copy(gracz.wynik['akcje'])


                    action = str(input(f"{gracz.nazwa} podejmij decyzje: "))
                    if action == 'zakup':
                        zakup = gracz.zakup()
                        if zakup[1] not in set(giełda.iloc[:,0]):
                            print("Błędna nazwa papieru")
                            continue
                        elif zakup[3] > giełda.loc[giełda['Nazwa']==zakup[1],'max'].iloc[0]:
                            print("Cena oferty wyższa od ceny maksymalnej")
                            continue
                        elif zakup[2]*zakup[3] > kasa:
                            print("Brak środków do zrealizowania transakcji")
                            continue
                        else:
                            print('udało się złożyć zlecenie')
                            zlecenia_kupno.append(zakup)
                            kasa -= zakup[2]*zakup[3]
                            try:
                                roznica = papiery[zakup[1]] + zakup[2]
                                papiery[zakup[1]] = roznica
                            except:
                                papiery[zakup[1]] = zakup[2]
                    elif action == "sprzedaz":
                        sprzedaz = gracz.sprzedaz()
                        if sprzedaz[1] not in papiery.keys():
                            print("Brak papieru do sprzedania")
                            continue
                        elif sprzedaz[3] < giełda.loc[giełda['Nazwa']==sprzedaz[1],'min'].iloc[0]:
                            print("Cena oferty sprzedazy nizsza niz cena minimalna")
                            continue
                        elif sprzedaz[2] > papiery[sprzedaz[1]]:
                            print("Brak pożądanej ilości papieru do sprzedania")
                            continue
                        else:
                            zlecenia_sprzedaz.append(sprzedaz)
                            kasa += sprzedaz[2]*sprzedaz[3]
                            try:

                                roznica = papiery[sprzedaz[1]] - sprzedaz[2]
                                papiery[sprzedaz[1]] = roznica
                            except:
                                papiery[sprzedaz[1]] = sprzedaz[2]
                    elif action =='stan konta':
                        gracz.stan_konta()
                    elif action == "":
                        continue
                    else:
                        print("Błędna komenda")

                if len(zlecenia_kupno) > 0:
                    ramka_zakup = pd.DataFrame(zlecenia_kupno,columns=['Gracz','papier','ilosc','cena'])

                    ramka_zakup['skumulowana_ilosc'] = ramka_zakup.papier.map(ramka_zakup.groupby('papier')['ilosc'].sum())

                    ramka_zakup = ramka_zakup.merge(giełda[['Nazwa','wolumen']],left_on = 'papier',right_on = 'Nazwa', how = 'inner').drop(columns='Nazwa')

                    ramka_zakup = ramka_zakup.assign(final_wolumen = np.where(ramka_zakup['skumulowana_ilosc'] > ramka_zakup['wolumen'],round((ramka_zakup['ilosc']/ramka_zakup['skumulowana_ilosc'])*ramka_zakup['wolumen']), ramka_zakup['ilosc']))



                if len(zlecenia_sprzedaz) > 0:
                    ramka_sprzedaz = pd.DataFrame(zlecenia_sprzedaz,columns=['Gracz','papier','ilosc','cena'])


                for gracz in self.gracze:
                    if len(zlecenia_kupno) >0:
                        try:

                            gracz.aktualizacja_zakup(ramka_zakup)

                        except:

                            pass

                    if len(zlecenia_sprzedaz) >0:
                        try:
                            gracz.aktualizacja_sprzedaz(ramka_sprzedaz)
                        except:
                            pass


                decyzja_dzien = input("Czy chcesz przejść do kolejnego dnia?: ")
                if decyzja_dzien =="tak":
                    while True:
                        try:
                            start_date += delta
                            day = str(start_date)
                            data = day[8:10] + '-' + day[5:7] + '-' + day[:4]
                            giełda = Giełda(data).wartosci
                            break
                        except:
                            start_date += delta
                            day = str(start_date)
                            data = day[8:10] + '-' + day[5:7] + '-' + day[:4]
                            pass


            except:
                print("błąd")




        print("Zakończono grę")
        print("Wynik końcowy graczy")

        for gracz in self.gracze:
            print(f"Gracz {gracz.nazwa} zaczynał grę z wkładem {gracz.wklad}. Grę zakończył z wynikiem {gracz.wynik['kapitał']}."
                  f"Stosunek wyniku końcowego do wkładu początkowego wynosi {round(gracz.wynik['kapitał']/gracz.wklad,2)}")

# Zdefiniowani przykładowi gracze i wkłady początkowe


Adrian = Gracz('Adrian',10000)
Bartosz = Gracz('Bartosz',30000)


# parametry wejściowe


rozgrywka = Gra('17-06-2021','18-06-2021',Adrian,Bartosz)


# inicjalizacja gry


rozgrywka.rozpocznij()

