import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ChevronDown, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Logo from "@/components/Logo";

const FAQPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [openItems, setOpenItems] = useState({});

  const toggleItem = (id) => {
    setOpenItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const faqCategories = [
    {
      title: "Général",
      items: [
        {
          id: "general-1",
          question: "Qu'est-ce que le GEO (Generative Engine Optimization) ?",
          answer: "Le GEO est l'optimisation de votre présence dans les réponses générées par les intelligences artificielles comme ChatGPT, Claude, Gemini ou Perplexity. Contrairement au SEO traditionnel qui optimise pour les moteurs de recherche, le GEO optimise pour les moteurs de réponse IA qui synthétisent l'information plutôt que de lister des liens."
        },
        {
          id: "general-2",
          question: "Pourquoi le GEO est-il important pour mon entreprise ?",
          answer: "De plus en plus d'utilisateurs interrogent directement les IA pour obtenir des recommandations. Si votre marque n'apparaît pas dans ces réponses, vous perdez des opportunités business. Le GEO vous permet de comprendre et d'améliorer votre visibilité dans ce nouveau canal de découverte."
        },
        {
          id: "general-3",
          question: "Comment fonctionne l'analyse IAskan ?",
          answer: "IAskan utilise le protocole IAskan Verified GEO Protocol™ : nous interrogeons plusieurs IA (ChatGPT, Claude, Gemini, Perplexity) avec des requêtes variées correspondant à votre secteur. Chaque requête est exécutée plusieurs fois pour mesurer la stabilité des résultats. Nous analysons ensuite la présence, le positionnement et le contexte de mention de votre marque."
        },
        {
          id: "general-4",
          question: "Qu'est-ce que le score R.A.T.E.™ ?",
          answer: "R.A.T.E.™ est notre méthodologie propriétaire qui évalue 4 dimensions : Relevance (pertinence contextuelle), Authority (autorité perçue), Truthfulness (exactitude des informations) et Endorsement (niveau de recommandation). Ce score composite de 0 à 100 reflète votre visibilité GEO globale."
        }
      ]
    },
    {
      title: "Tarifs & Abonnements",
      items: [
        {
          id: "pricing-1",
          question: "Puis-je essayer IAskan gratuitement ?",
          answer: "Oui ! Nous offrons un essai gratuit comprenant 1 scan complet avec 10 prompts sur 2 IA (ChatGPT et Claude). C'est suffisant pour découvrir la valeur de l'analyse GEO pour votre marque. L'essai est limité à un par utilisateur/entreprise."
        },
        {
          id: "pricing-2",
          question: "Quelle est la différence entre les plans ?",
          answer: "Les plans diffèrent par : le nombre de scans mensuels (10 à 150), le nombre de prompts par scan (10 à 200), le nombre d'IA analysées (2 à 4), les runs par requête (3 à 5 pour la stabilité), et les fonctionnalités avancées (génération de contenu, API, support dédié)."
        },
        {
          id: "pricing-3",
          question: "Les quotas non utilisés sont-ils reportés ?",
          answer: "Non, les quotas de scans et de requêtes sont mensuels et ne sont pas reportables au mois suivant. Nous vous recommandons de choisir un plan adapté à votre usage réel."
        },
        {
          id: "pricing-4",
          question: "Comment puis-je changer de plan ?",
          answer: "Vous pouvez upgrader ou downgrader à tout moment depuis les paramètres de votre compte. L'upgrade est immédiat, le downgrade prend effet à la prochaine période de facturation."
        },
        {
          id: "pricing-5",
          question: "Proposez-vous des tarifs annuels ?",
          answer: "Oui, contactez-nous pour obtenir un devis personnalisé avec une réduction pour un engagement annuel. Les entreprises peuvent également bénéficier de tarifs sur mesure."
        }
      ]
    },
    {
      title: "Analyse & Résultats",
      items: [
        {
          id: "analysis-1",
          question: "Combien de temps dure une analyse ?",
          answer: "Une analyse complète prend généralement entre 2 et 10 minutes selon le nombre de prompts et d'IA configurés. Vous pouvez naviguer ailleurs pendant l'analyse et vous serez notifié quand elle sera terminée."
        },
        {
          id: "analysis-2",
          question: "Que signifient les différents indices (Stability, Dominance, etc.) ?",
          answer: "Stability Index™ mesure la cohérence des réponses IA sur plusieurs runs. Dominance Index™ compare votre visibilité à celle de vos concurrents. Trust Gap™ évalue l'écart entre votre score et celui du leader. Opportunity Score™ identifie votre potentiel d'amélioration."
        },
        {
          id: "analysis-3",
          question: "Pourquoi les résultats varient-ils entre deux analyses ?",
          answer: "Les IA ne sont pas déterministes : elles peuvent donner des réponses différentes à la même question. C'est pourquoi nous effectuons plusieurs runs par requête et calculons un indice de stabilité. Des variations modérées sont normales."
        },
        {
          id: "analysis-4",
          question: "Comment interpréter le benchmark concurrentiel ?",
          answer: "Le benchmark montre les marques qui apparaissent le plus souvent dans les réponses IA pour vos mots-clés. Un concurrent avec plus de mentions n'est pas forcément meilleur, mais plus visible sur ce type de requêtes. Analysez le contexte de leurs mentions pour comprendre pourquoi."
        }
      ]
    },
    {
      title: "Optimisation & Recommandations",
      items: [
        {
          id: "optim-1",
          question: "Comment améliorer mon score GEO ?",
          answer: "Les principales leviers sont : enrichir votre contenu avec des données structurées (Schema.org), créer une FAQ complète, publier du contenu expert régulièrement, obtenir des citations et backlinks de sources autoritaires, et s'assurer que vos informations sont cohérentes partout en ligne."
        },
        {
          id: "optim-2",
          question: "Qu'est-ce que la 'citabilité' ?",
          answer: "La citabilité mesure à quel point votre contenu est facile à citer par une IA. Un contenu bien structuré, factuel, avec des données Schema.org et des informations claires sera plus facilement repris par les modèles de langage."
        },
        {
          id: "optim-3",
          question: "Les recommandations sont-elles personnalisées ?",
          answer: "Oui, chaque recommandation est générée en fonction de vos résultats spécifiques. Nous priorisons les actions par impact potentiel et effort requis pour vous aider à concentrer vos ressources efficacement."
        },
        {
          id: "optim-4",
          question: "Combien de temps pour voir des améliorations ?",
          answer: "Cela dépend des actions entreprises. Les corrections d'informations incorrectes peuvent avoir un effet en quelques semaines. L'amélioration de la citabilité par le contenu peut prendre 1-3 mois. La construction d'autorité est un travail de fond sur 6-12 mois."
        }
      ]
    },
    {
      title: "Technique & Sécurité",
      items: [
        {
          id: "tech-1",
          question: "Mes données sont-elles sécurisées ?",
          answer: "Oui, nous utilisons le chiffrement SSL/TLS pour toutes les communications, vos données sont stockées de manière sécurisée, et nous sommes conformes au RGPD. Nous ne partageons jamais vos données avec des tiers à des fins commerciales."
        },
        {
          id: "tech-2",
          question: "Proposez-vous une API ?",
          answer: "Oui, le plan Business inclut l'accès à notre API REST pour intégrer les analyses GEO dans vos propres outils et workflows. La documentation complète est disponible dans votre espace client."
        },
        {
          id: "tech-3",
          question: "Quelles IA sont analysées ?",
          answer: "Nous analysons ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google) et Perplexity. Le nombre d'IA dépend de votre plan. Nous ajoutons régulièrement de nouvelles IA au fur et à mesure de leur adoption."
        }
      ]
    }
  ];

  const filteredCategories = faqCategories.map(category => ({
    ...category,
    items: category.items.filter(item =>
      item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.items.length > 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="border-b border-slate-100 bg-white/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/">
            <Logo />
          </Link>
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-slate-900 mb-4">Questions Fréquentes</h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            Trouvez rapidement les réponses à vos questions sur IAskan et l'optimisation GEO.
          </p>
          
          {/* Search */}
          <div className="relative max-w-md mx-auto">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Rechercher une question..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none transition-all"
            />
          </div>
        </div>

        {/* FAQ Categories */}
        <div className="space-y-8">
          {filteredCategories.map((category, catIndex) => (
            <div key={catIndex}>
              <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-violet-500"></span>
                {category.title}
              </h2>
              <Card className="divide-y divide-slate-100">
                {category.items.map((item) => (
                  <div key={item.id} className="p-0">
                    <button
                      onClick={() => toggleItem(item.id)}
                      className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
                    >
                      <span className="font-medium text-slate-900 pr-4">{item.question}</span>
                      <ChevronDown className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform ${openItems[item.id] ? 'rotate-180' : ''}`} />
                    </button>
                    {openItems[item.id] && (
                      <div className="px-6 pb-4">
                        <p className="text-slate-600 leading-relaxed">{item.answer}</p>
                      </div>
                    )}
                  </div>
                ))}
              </Card>
            </div>
          ))}
        </div>

        {/* Contact CTA */}
        <div className="mt-12 p-8 bg-gradient-to-r from-violet-50 to-cyan-50 rounded-2xl text-center">
          <h3 className="text-xl font-semibold text-slate-900 mb-2">Vous n'avez pas trouvé votre réponse ?</h3>
          <p className="text-slate-600 mb-4">Notre équipe est disponible pour répondre à toutes vos questions.</p>
          <Link to="/contact">
            <Button className="bg-gradient-to-r from-violet-600 to-cyan-600">
              Contactez-nous
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
};

export default FAQPage;
