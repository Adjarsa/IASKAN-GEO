import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Logo from "@/components/Logo";

const TermsPage = () => {
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
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Conditions Générales de Vente</h1>
        
        <div className="prose prose-slate max-w-none">
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 1 - Objet</h2>
            <p className="text-slate-700">
              Les présentes Conditions Générales de Vente (CGV) régissent les relations contractuelles 
              entre IAskan SAS et tout utilisateur souscrivant à un abonnement sur la plateforme IAskan, 
              service de Generative Engine Optimization (GEO).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 2 - Services proposés</h2>
            <p className="text-slate-700 mb-4">IAskan propose les services suivants :</p>
            <ul className="list-disc pl-6 text-slate-700">
              <li>Analyse de visibilité de marque dans les réponses IA (ChatGPT, Claude, Gemini, Perplexity)</li>
              <li>Score GEO propriétaire R.A.T.E.™ (Relevance, Authority, Truthfulness, Endorsement)</li>
              <li>Indices exclusifs : Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™</li>
              <li>Benchmark concurrentiel automatisé</li>
              <li>Recommandations d'optimisation personnalisées</li>
              <li>Génération de contenu optimisé GEO</li>
              <li>Rapports PDF détaillés</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 3 - Offres et tarifs</h2>
            
            <h3 className="text-lg font-medium text-slate-800 mb-2">3.1 Essai gratuit</h3>
            <p className="text-slate-700 mb-4">
              Un essai gratuit unique est proposé aux nouveaux utilisateurs. Cet essai est limité à un 
              scan par utilisateur, domaine, adresse IP et appareil. Toute tentative de contournement 
              entraînera la suspension du compte.
            </p>

            <h3 className="text-lg font-medium text-slate-800 mb-2">3.2 Abonnements payants</h3>
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border border-slate-200 rounded-lg">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-slate-700">Plan</th>
                    <th className="px-4 py-2 text-left text-slate-700">Prix/mois</th>
                    <th className="px-4 py-2 text-left text-slate-700">Scans</th>
                    <th className="px-4 py-2 text-left text-slate-700">Projets</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-2">Starter</td>
                    <td className="px-4 py-2">79 €</td>
                    <td className="px-4 py-2">10/mois</td>
                    <td className="px-4 py-2">1</td>
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-2">Pro</td>
                    <td className="px-4 py-2">149 €</td>
                    <td className="px-4 py-2">50/mois</td>
                    <td className="px-4 py-2">5</td>
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-2">Business</td>
                    <td className="px-4 py-2">349 €</td>
                    <td className="px-4 py-2">150/mois</td>
                    <td className="px-4 py-2">Illimité</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-slate-700">
              Les prix sont indiqués en euros HT. La TVA applicable sera ajoutée lors du paiement.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 4 - Paiement</h2>
            <p className="text-slate-700 mb-4">
              Le paiement s'effectue par carte bancaire via notre prestataire sécurisé Stripe. 
              L'abonnement est facturé mensuellement, à date anniversaire de la souscription.
            </p>
            <p className="text-slate-700">
              Les quotas non utilisés ne sont pas reportables au mois suivant.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 5 - Durée et résiliation</h2>
            <p className="text-slate-700 mb-4">
              L'abonnement est conclu pour une durée indéterminée avec facturation mensuelle. 
              Vous pouvez résilier à tout moment depuis votre espace client. La résiliation prend 
              effet à la fin de la période de facturation en cours.
            </p>
            <p className="text-slate-700">
              En cas de non-paiement, l'accès au service sera suspendu après 7 jours de relance.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 6 - Droit de rétractation</h2>
            <p className="text-slate-700">
              Conformément à l'article L221-28 du Code de la consommation, le droit de rétractation 
              ne s'applique pas aux services pleinement exécutés avant la fin du délai de rétractation 
              et dont l'exécution a commencé avec l'accord du consommateur. En souscrivant à un 
              abonnement IAskan, vous reconnaissez renoncer expressément à votre droit de rétractation 
              dès le premier scan effectué.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 7 - Propriété intellectuelle</h2>
            <p className="text-slate-700 mb-4">
              Les rapports et données générés par IAskan vous sont concédés en licence d'utilisation 
              non exclusive pour votre usage interne uniquement.
            </p>
            <p className="text-slate-700">
              La technologie, les algorithmes, les marques et le protocole IAskan Verified GEO Protocol™ 
              restent la propriété exclusive de IAskan SAS.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 8 - Limitation de responsabilité</h2>
            <p className="text-slate-700 mb-4">
              IAskan fournit un service d'analyse et de recommandations à titre informatif. 
              Les résultats dépendent de nombreux facteurs externes (évolution des algorithmes IA, 
              concurrence, etc.) et ne garantissent pas un positionnement spécifique.
            </p>
            <p className="text-slate-700">
              La responsabilité de IAskan SAS ne pourra excéder le montant des sommes versées au 
              cours des 12 derniers mois.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 9 - Disponibilité du service</h2>
            <p className="text-slate-700">
              IAskan s'engage à fournir un service disponible 99% du temps (hors maintenance programmée). 
              En cas d'interruption prolongée (&gt;24h), un avoir sera accordé au prorata.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 10 - Modification des CGV</h2>
            <p className="text-slate-700">
              IAskan SAS se réserve le droit de modifier les présentes CGV. Les modifications 
              seront notifiées par email 30 jours avant leur entrée en vigueur. La poursuite de 
              l'utilisation du service vaut acceptation des nouvelles conditions.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Article 11 - Droit applicable et litiges</h2>
            <p className="text-slate-700 mb-4">
              Les présentes CGV sont soumises au droit français. En cas de litige, une solution 
              amiable sera recherchée avant toute action judiciaire.
            </p>
            <p className="text-slate-700">
              Conformément aux dispositions du Code de la consommation, vous pouvez recourir 
              gratuitement au service de médiation MEDICYS : <a href="https://www.medicys.fr" target="_blank" rel="noopener noreferrer" className="text-violet-600 hover:underline">www.medicys.fr</a>
            </p>
            <p className="text-slate-700 mt-4">
              À défaut de résolution amiable, les tribunaux de Paris seront seuls compétents.
            </p>
          </section>
        </div>

        <p className="text-sm text-slate-500 mt-12">
          Dernière mise à jour : {new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}
        </p>
      </main>
    </div>
  );
};

export default TermsPage;
