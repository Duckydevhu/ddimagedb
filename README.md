# ddimagedb
Képfájl-kezelő Alkalmazás - Felhasználói Kézikönyv
Mi ez a program?
Ez az alkalmazás segít képfájljaid kezelésében és kategorizálásában. A program képes:

Képfájlok automatikus beolvasására megadott mappákból
Mesterséges intelligencia (AI) segítségével kulcsszavak generálására a képekhez
Nyomon követni, hogy mely képeket használtad már fel
Keresni és szűrni a képeket különböző szempontok szerint


Program indítása

Indítsd el a programot (dupla kattintás az alkalmazáson)
Két fül jelenik meg: Beállítások és Adatok


1. Beállítások lap - Első lépések
FONTOS: Ezeket mindenképpen állítsd be!
1.1 Mappa útvonalak megadása

Mit írj be: Azoknak a mappáknak a teljes elérési útja, ahol a képeid vannak
Hogyan: Minden mappát új sorba írj
Példa:

  C:\Felhasználók\SajátNeved\Képek
  D:\Fényképek\Vakáció
1.2 Google AI Studio API kulcs

Mire való: Ez szükséges ahhoz, hogy az AI kulcsszavakat tudjon generálni a képeidhez
Hogyan szerezd be:

Menj a Google AI Studio weboldalra
Jelentkezz be Google fiókkal
Hozz létre egy API kulcsot
Másold be ide (csillagokkal jelenik meg a biztonság érdekében)



1.3 AI Prompt Sablon

Mit csinál: Ez az utasítás mondja meg az AI-nak, hogy mit kérdezzen meg a képről
Alapértelmezett szöveg: Már van beállítva egy jó példa, ami 10 kulcsszót kér minden képről
Módosítható: Ha szeretnéd, átírhatod, hogy más információkat kapj (pl. több/kevesebb kulcsszó, más nyelv, stb.)

1.4 Mentés

Kattints a "Mentés" gombra, hogy a beállításaid elmentődjenek
Ha sikerült, egy üzenet jelenik meg: "A beállítások sikeresen elmentve!"


2. Adatok lap - Képek kezelése
2.1 Mappák beolvasása

Kattints a "Mappák beolvasása" gombra
A program végignézi a beállított mappákat
Az összes képfájlt (.jpg, .png, .gif, stb.) hozzáadja az adatbázishoz
A bal oldali szövegdobozban láthatod, mi történik
Fontos: Csak az új fájlokat adja hozzá, a már meglévőket nem duplikálja

2.2 A táblázat oszlopai
A program 4 oszlopban tárolja az információkat:
Oszlop neveMit jelentFájl útvonalA kép teljes elérési útja a gépenAI kulcsszavakAz AI által generált leíró szavakFelhasználás dátumaMikor jelölted felhasználtnak (pl. 2025.10.02)FelhasználvaIgen/Nem - használtad-e már ezt a képet
2.3 Kép előnézet

Amikor rákattintasz egy sorra a táblázatban, a jobb oldalon megjelenik a kép kis előnézete (250×250 pixel)
Így gyorsan megnézheted, melyik képről van szó


3. Keresés és szűrés
A táblázat felett találod a szűrőmezőket:
3.1 Egyszerű keresés

Fájl útvonal: Írj be egy szövegrészt, amit a fájl nevében keresel (pl. "vakáció")
AI kulcsszavak: Keress a kulcsszavak között (pl. "tenger")

3.2 Dátum szerinti szűrés

Dátum szűrés típusa:

Nincs - nem szűr dátum szerint
Korábbi, mint - a megadott dátumnál régebbi
Későbbi, mint - a megadott dátumnál újabb
Közte - két dátum között


Dátum formátum: ÉÉÉÉ.HH.NN (pl. 2025.10.02)

3.3 Egyéb szűrők

ÉS/VAGY: Hogyan kombinálódnak a keresési feltételek

ÉS: Minden feltételnek teljesülnie kell
VAGY: Elég, ha egy feltétel teljesül


Felhasználva:

Mind - minden kép
Igen - csak a felhasználtak
Nem - csak a még fel nem használtak


Elemek száma: Hány sort mutasson (pl. 10, 50, 100)

3.4 Keresés indítása

Kattints a "Betöltés" gombra vagy nyomj Enter-t a mezőkben
A táblázat frissül az új találatokkal


4. Adatok szerkesztése
4.1 Kulcsszavak és dátum kézi szerkesztése

Dupla kattintás az "AI kulcsszavak" vagy "Felhasználás dátuma" cellán
Szerkesztőmező jelenik meg
Írd át, amit szeretnél
Nyomj Enter-t a mentéshez

4.2 Felhasználva állapot gyors váltása

Dupla kattintás a "Felhasználva" oszlopban
Automatikusan vált Igen ↔ Nem között
Ha Igen-re váltasz, a mai dátum beíródik
Ha Nem-re váltasz, a dátum törlődik

4.3 Tömeges műveletek
Kijelölés: Kattints egy sorra, majd:

Ctrl + kattintás - további sorok kijelölése egyesével
Shift + kattintás - sorozat kijelölése

Tömeges gombok:

Kijelöltek beállítása: Igen - Minden kijelölt kép felhasználttá válik (mai dátummal)
Kijelöltek beállítása: Nem - Minden kijelölt kép vissza nem használtra (dátum törlése)
AI kulcsszavak feltöltése - AI generál kulcsszavakat a kijelölt képekhez
Kijelöltek törlése - Véglegesen törli a kijelölt sorokat az adatbázisból

4.4 Változtatások mentése

Minden szerkesztés után a "Változtatások mentése" gomb aktívvá válik
FONTOS: Kattints rá, különben az adatbázisba nem kerülnek be a módosítások!
Csak a memóriában vannak a változások, amíg nem mented el


5. AI kulcsszavak generálása
5.1 Hogyan működik?

Jelölj ki egy vagy több képet a táblázatban
Kattints az "AI kulcsszavak feltöltése" gombra
A program minden kijelölt képről:

Elküldi az AI-nak
Az AI elemzi a képet
Kulcsszavakat generál (az általad beállított prompt szerint)
Beírja a táblázatba



5.2 Várakozás

Ez időigényes művelet (kb. 1-2 másodperc képenként)
A bal oldali állapotablakban láthatod, hol tart
A gomb inaktív lesz, amíg fut a művelet

5.3 Mentés

Ne feledd: a generálás után kattints a "Változtatások mentése" gombra!


6. Exportálás
CSV exportálás

Kattints a "Teljes DB exportálása CSV-be" gombra
Válaszd ki, hová szeretnéd menteni
Az egész adatbázis kiexportálódik Excel-ben is megnyitható formátumba


7. Rendezés

Kattints bármelyik oszlop fejlécére a táblázatban
Először növekvő sorrendbe rendez (A→Z)
Újabb kattintásra csökkenő sorrend (Z→A)
A nyíl jelzi az aktuális rendezést


8. Tippek és trükkök
✅ Jó gyakorlatok

Rendszeresen mentsd el a változtatásokat
Használd a szűrőket a gyors kereséshez
Jelöld meg "Felhasználva"-ként a képeket, amiket már használtál projekten
Az AI kulcsszavak segítenek később megtalálni a képeket

⚠️ Figyelmeztetések

Az adatbázisból való törlés végleges - a képfájlt nem törli, de az információt igen
Az AI kulcsszó generálás költséggel járhat (Google AI API díjszabás szerint)
Nagyon sok kép esetén (több ezer) az AI generálás sokáig tarthat

💡 Hasznos tudnivalók

A program automatikusan menti a beállításokat kilépéskor
Az oszlopszélességek is mentődnek
A szűrőbeállítások megmaradnak újraindítás után


9. Hibaelhárítás
"Nem sikerült kapcsolódni az adatbázishoz"

Ellenőrizd, hogy van-e írási jogod a program mappájában

"Hiba az AI kulcsszavak generálása során"

Ellenőrizd az API kulcsot a Beállítások lapon
Lehet, hogy elfogyott az ingyenes kvótád a Google AI-nál

"Érvénytelen dátum formátum"

A dátumokat így add meg: ÉÉÉÉ.HH.NN (pl. 2025.10.02)

Kép nem jelenik meg az előnézetben

Ellenőrizd, hogy a fájl még létezik-e az adott helyen
Lehet, hogy áthelyezted vagy törölted


10. Gyors kezdés - Lépésről lépésre

Indítás után → Beállítások lap
Add meg a mappák elérési útját
Add meg a Google API kulcsot
Mentés gomb → Adatok lap
Mappák beolvasása gomb
Jelölj ki néhány képet
AI kulcsszavak feltöltése gomb
Várj, amíg végez
Változtatások mentése gomb
Kész! Most már tudsz keresni és szűrni


Kellemes használatot! 😊
