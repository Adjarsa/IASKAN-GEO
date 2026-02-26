import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Logo from "@/components/Logo";

const LegalPage = () => {
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
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Mentions Légales</h1>
        
        <div className="prose prose-slate max-w-none">
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">1. Éditeur du site</h2>
            <p className="text-slate-700 mb-4">
              Le site IAskan est édité par :
            </p>
            <ul className="list-none space-y-2 text-slate-700">
              <li><strong>Raison sociale :</strong> IAskan SAS</li>
              <li><strong>Forme juridique :</strong> Société par Actions Simplifiée</li>
              <li><strong>Capital social :</strong> 10 000 €</li>
              <li><strong>Siège social :</strong> 123 Avenue de l'Innovation, 75001 Paris, France</li>
              <li><strong>RCS :</strong> Paris B 123 456 789</li>
              <li><strong>N° TVA Intracommunautaire :</strong> FR 12 345678901</li>
              <li><strong>Directeur de la publication :</strong> [Nom du dirigeant]</li>
              <li><strong>Email :</strong> contact@iaskan.com</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">2. Hébergement</h2>
            <p className="text-slate-700 mb-4">
              Le site est hébergé par :
            </p>
            <ul className="list-none space-y-2 text-slate-700">
              <li><strong>Hébergeur :</strong> Emergent Labs</li>
              <li><strong>Adresse :</strong> Services Cloud</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">3. Propriété intellectuelle</h2>
            <p className="text-slate-700 mb-4">
              L'ensemble des éléments figurant sur le site IAskan (textes, graphismes, logos, icônes, images, 
              clips audio et vidéo, logiciels, bases de données) sont la propriété exclusive de IAskan SAS 
              ou de ses partenaires.
            </p>
            <p className="text-slate-700 mb-4">
              Toute reproduction, représentation, modification, publication, adaptation de tout ou partie 
              des éléments du site, quel que soit le moyen ou le procédé utilisé, est interdite, sauf 
              autorisation écrite préalable de IAskan SAS.
            </p>
            <p className="text-slate-700">
              Les marques "IAskan", "IAskan Verified GEO Protocol™", "R.A.T.E.™", "Stability Index™", 
              "Dominance Index™", "Trust Gap™" et "Opportunity Score™" sont des marques déposées.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">4. Limitation de responsabilité</h2>
            <p className="text-slate-700 mb-4">
              IAskan SAS s'efforce d'assurer au mieux l'exactitude et la mise à jour des informations 
              diffusées sur ce site, dont elle se réserve le droit de corriger le contenu à tout moment 
              et sans préavis.
            </p>
            <p className="text-slate-700">
              IAskan SAS décline toute responsabilité en cas d'interruption du site, de survenance de 
              bugs ou d'erreurs de fonctionnement, ainsi que pour tout dommage résultant d'une intrusion 
              frauduleuse d'un tiers.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">5. Droit applicable</h2>
            <p className="text-slate-700">
              Les présentes mentions légales sont soumises au droit français. En cas de litige, 
              les tribunaux français seront seuls compétents.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">6. Contact</h2>
            <p className="text-slate-700">
              Pour toute question relative aux présentes mentions légales, vous pouvez nous contacter à 
              l'adresse suivante : <a href="mailto:legal@iaskan.com" className="text-violet-600 hover:underline">legal@iaskan.com</a>
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

export default LegalPage;
