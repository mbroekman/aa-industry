--- 
name: commit
description: Inspecteer huidige worktree en maak een nauwkeurige conventional git commit voor deze repository
---

Gebruik deze skill wanneerr de gebruiker een git commit wil voorbereiden of aanmakne voor de huidige repository

werkwijze:
1. inspecteer 'git status' en de diff
2. Bepaal de kleinste samenhangende scope voor de commit
3. bepaal het commit type, bij voorkeur conventional commit types: 'feat', 'fix', 'chore', 'docs', 'style', 'test', 'refactor', 'perf', 'build', 'ci', 'revert'
4. schrijf de commit message op conventional commit formaat in het engels
5. Als de wijzigingen onduidelijk zijn of uit meerdere onderwerpen bestaat, le de opties uit voor je commit
6. Voeg geen niet-gerelateerde bestanden toe aan de commit
7. Vraag bevestiging aan de gebruiker alvorens de commit uit te voeren en toon de diff met "git diff" bij bevestiging
8. Voer de commit uit op basis van de commit message
9. Schoon de tijdelijke bestanden op die mogelijk aangemaakt zijn tijdens deze aanpassingen
10. Geef aan of de commit gelukt is en geef een overzicht van de werkboom, inclusief welke bestanden unchanged zijn