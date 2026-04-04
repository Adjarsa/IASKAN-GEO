# AUDIT CONSOLIDÉ IAskan GEO Platform
## Date: 16 Mars 2026

---

## SYNTHÈSE EXÉCUTIVE

L'audit Claude Opus a identifié des problèmes critiques valides. Ce document consolide l'analyse et propose un plan d'action priorisé et réaliste.

### Verdict Global
**IAskan est à 60% de son potentiel.** Les fondations sont solides (pipeline 13 phases, scoring R.A.T.E., architecture modulaire), mais des problèmes de crédibilité technique et d'UX freinent sa commercialisation.

---

## PROBLÈMES CRITIQUES CONFIRMÉS

### 1. 🔴 Perplexity est FAUX (CRITIQUE)
**Fichier:** `/app/backend/app/services/llm_connector.py` lignes 36-40
```python
"perplexity": {
    "provider": "openai",
    "model": "gpt-4o-mini",  # ← FAUX ! C'est OpenAI, pas Perplexity
    "display_name": "Perplexity"
}
```
**Impact:** Le client Pro paie pour 4 IA mais n'en a que 3. Risque de crédibilité fatal.
**Solution:** Intégrer la vraie API Perplexity (sonar-pro) ou remplacer par Mistral/DeepSeek.

### 2. 🔴 Modèle Claude potentiellement obsolète
**Fichier:** `/app/backend/app/services/llm_connector.py` ligne 28
```python
"model": "claude-sonnet-4-5-20250929"
```
**Vérification requise:** Ce modèle existe-t-il dans l'API Anthropic actuelle ?

### 3. 🔴 Mock Data en Production (10 occurrences)
**Fichiers concernés:**
- `ContentAuditPage.jsx`: `getMockAuditData()` (lignes 64-134)
- `ArticleOptimizerPage.jsx`: `generateMockOptimizations()`, `generateMockContent()` (6 occurrences)

**Impact:** Un client payant voit des données fictives. INACCEPTABLE.

### 4. 🟠 server.py Monolithique (4662 lignes)
**Problème:** Code dupliqué entre server.py et `/app/routers/`. 26 blocs `except Exception` avalent les erreurs.
**Impact:** Maintenance difficile, bugs silencieux.

### 5. 🟠 Pas de Rate Limiting API
**Vérification:** Aucun middleware de throttling trouvé.
**Impact:** Vulnérable au DDoS et à l'abus de l'API.

### 6. 🟠 CORS_ORIGINS = '*' possible
**Fichier:** `/app/backend/app/core/config.py`
```python
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
```
**Impact:** Faille de sécurité potentielle si non configuré en production.

---

## PROBLÈMES ALGORITHMIQUES

### 7. Score GEO factice dans le générateur
L'audit mentionne `geo_score = min(95, 75 + keywords*2)` - À vérifier dans le code actuel.

### 8. Détection de marque trop simple
```python
brand_mentioned = brand_lower in response_lower  # Keyword matching basique
```
**Rate:** Variantes, acronymes, fautes d'orthographe.
**Solution:** Utiliser embeddings ou NER (spaCy).

### 9. Recommandations génériques
Templates hardcodés, pas de contextualisation par LLM.

---

## UX/NAVIGATION

### 10. 11 entrées de menu = parcours confus
**Actuel:** Dashboard, Analyses, Visibilité, Audit Contenu, Optimiseur GEO, Générateur, Benchmark, Évolution, Recommandations, Organisation, Paramètres

**Proposition Opus (4 écrans):**
1. **AUDIT** - Lancer scan + voir résultats
2. **CONCURRENCE** - Benchmark + comparatif
3. **ACTIONS** - Recommandations + Optimiseur + Générateur
4. **SUIVI** - Historique + Alertes + Rapports

---

## PLAN D'ACTION CONSOLIDÉ

### SPRINT 1 - CRÉDIBILITÉ (Semaine 1-2) [URGENT]

| Tâche | Priorité | Effort | Impact |
|-------|----------|--------|--------|
| Intégrer vraie API Perplexity (sonar-pro) | P0 | 4h | CRITIQUE |
| Vérifier/corriger modèle Claude | P0 | 1h | CRITIQUE |
| Supprimer TOUTES les mock data | P0 | 2h | CRITIQUE |
| Ajouter rate limiting (SlowAPI) | P1 | 2h | Sécurité |
| Configurer CORS proprement | P1 | 30min | Sécurité |

### SPRINT 2 - ARCHITECTURE (Semaine 3-4)

| Tâche | Priorité | Effort | Impact |
|-------|----------|--------|--------|
| Migrer routes de server.py vers /routers | P1 | 8h | Maintenance |
| Implémenter cache Redis pour LLM | P1 | 4h | Performance |
| Supprimer code MongoDB résiduel | P2 | 2h | Nettoyage |
| Améliorer gestion exceptions (pas de except Exception) | P2 | 3h | Debug |

### SPRINT 3 - ALGORITHME (Semaine 5-6)

| Tâche | Priorité | Effort | Impact |
|-------|----------|--------|--------|
| Supprimer formule geo_score factice | P0 | 2h | Crédibilité |
| Upgrader détection marque avec embeddings | P1 | 6h | Précision |
| Recommandations contextualisées par LLM | P1 | 4h | Valeur |
| Génération dynamique de queries par LLM | P2 | 4h | Pertinence |

### SPRINT 4 - GEO ACTION ENGINE (Semaine 7-10)

| Tâche | Priorité | Effort | Impact |
|-------|----------|--------|--------|
| GEO Content Engine (génération optimisée) | P1 | 16h | Différenciation |
| Structured Data Generator (schema.org) | P1 | 8h | SEO IA |
| Monitoring continu + Alertes | P2 | 12h | Rétention |
| Source Seeding Strategy | P2 | 8h | Différenciation |

### SPRINT 5 - UX REFONTE (Semaine 11-12)

| Tâche | Priorité | Effort | Impact |
|-------|----------|--------|--------|
| Refondre navigation en 4 écrans | P1 | 8h | UX |
| Onboarding en 3 clics | P1 | 4h | Conversion |
| Intégrer React Query + Zustand | P2 | 6h | Performance |

---

## CORRECTIONS IMMÉDIATES POSSIBLES MAINTENANT

1. **Perplexity → Vraie API** (via integration_playbook)
2. **Supprimer mock data** (ContentAuditPage, ArticleOptimizerPage)
3. **Ajouter rate limiting** (SlowAPI)
4. **Corriger CORS** (configurer explicitement)

---

## MODULES MANQUANTS (Roadmap)

### Priorité 1: GEO Content Engine
Générer du contenu spécifiquement conçu pour être cité par les LLM.

### Priorité 2: Source Seeding Strategy
Identifier les sources que les LLM citent et y positionner la marque.

### Priorité 3: Structured Data Generator
Générer le markup schema.org automatiquement.

### Priorité 4: Monitoring Continu + Alertes
Scans hebdomadaires automatiques avec alertes email/Slack.

---

## CONCLUSION

L'audit Opus est **pertinent et actionnable**. Les priorités absolues sont:

1. **Corriger Perplexity** (crédibilité)
2. **Supprimer mock data** (crédibilité)
3. **Rate limiting + CORS** (sécurité)
4. **Refactoring server.py** (maintenabilité)

Une fois ces 4 points résolus, IAskan sera prêt pour une commercialisation sérieuse.
