import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Logo from "@/components/Logo";

const PrivacyPage = () => {
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
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Politique de Confidentialité</h1>
        
        <div className="prose prose-slate max-w-none">
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">1. Introduction</h2>
            <p className="text-slate-700 mb-4">
              IAskan SAS ("nous", "notre", "nos") s'engage à protéger votre vie privée. Cette politique 
              de confidentialité explique comment nous collectons, utilisons, stockons et protégeons vos 
              données personnelles lorsque vous utilisez notre plateforme de Generative Engine Optimization (GEO).
            </p>
            <p className="text-slate-700">
              En utilisant IAskan, vous acceptez les pratiques décrites dans cette politique.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">2. Données collectées</h2>
            <p className="text-slate-700 mb-4">Nous collectons les types de données suivants :</p>
            
            <h3 className="text-lg font-medium text-slate-800 mb-2">2.1 Données d'identification</h3>
            <ul className="list-disc pl-6 text-slate-700 mb-4">
              <li>Nom et prénom</li>
              <li>Adresse email</li>
              <li>Photo de profil (si connexion via SSO)</li>
              <li>Nom de l'entreprise (optionnel)</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mb-2">2.2 Données d'utilisation</h3>
            <ul className="list-disc pl-6 text-slate-700 mb-4">
              <li>Projets créés et analysés</li>
              <li>Historique des analyses GEO</li>
              <li>Préférences utilisateur</li>
              <li>Logs de connexion</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mb-2">2.3 Données techniques</h3>
            <ul className="list-disc pl-6 text-slate-700">
              <li>Adresse IP</li>
              <li>Type de navigateur</li>
              <li>Empreinte numérique (fingerprint) pour la sécurité anti-abus</li>
              <li>Cookies de session</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">3. Utilisation des données</h2>
            <p className="text-slate-700 mb-4">Vos données sont utilisées pour :</p>
            <ul className="list-disc pl-6 text-slate-700">
              <li>Fournir et améliorer nos services d'analyse GEO</li>
              <li>Gérer votre compte et abonnement</li>
              <li>Vous envoyer des notifications relatives à vos analyses</li>
              <li>Prévenir les fraudes et abus (notamment pour l'essai gratuit)</li>
              <li>Générer des statistiques anonymisées d'utilisation</li>
              <li>Respecter nos obligations légales</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">4. Partage des données</h2>
            <p className="text-slate-700 mb-4">
              Nous ne vendons jamais vos données personnelles. Nous pouvons les partager avec :
            </p>
            <ul className="list-disc pl-6 text-slate-700">
              <li><strong>Prestataires de services :</strong> Hébergement (Emergent Labs), paiement (Stripe), 
                email (Resend)</li>
              <li><strong>Services d'IA :</strong> OpenAI, Anthropic, Google pour l'analyse GEO (données 
                anonymisées)</li>
              <li><strong>Autorités légales :</strong> Si requis par la loi</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">5. Durée de conservation</h2>
            <ul className="list-disc pl-6 text-slate-700">
              <li><strong>Données de compte :</strong> Conservées tant que votre compte est actif, 
                puis 3 ans après la dernière connexion</li>
              <li><strong>Données d'analyse :</strong> 2 ans après la dernière utilisation</li>
              <li><strong>Logs de sécurité :</strong> 1 an</li>
              <li><strong>Données de facturation :</strong> 10 ans (obligation légale)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">6. Vos droits (RGPD)</h2>
            <p className="text-slate-700 mb-4">
              Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des droits suivants :
            </p>
            <ul className="list-disc pl-6 text-slate-700">
              <li><strong>Droit d'accès :</strong> Obtenir une copie de vos données</li>
              <li><strong>Droit de rectification :</strong> Corriger vos données inexactes</li>
              <li><strong>Droit à l'effacement :</strong> Demander la suppression de vos données</li>
              <li><strong>Droit à la portabilité :</strong> Recevoir vos données dans un format structuré</li>
              <li><strong>Droit d'opposition :</strong> Vous opposer au traitement de vos données</li>
              <li><strong>Droit à la limitation :</strong> Limiter le traitement de vos données</li>
            </ul>
            <p className="text-slate-700 mt-4">
              Pour exercer ces droits, contactez-nous à : <a href="mailto:privacy@iaskan.com" className="text-violet-600 hover:underline">privacy@iaskan.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">7. Cookies</h2>
            <p className="text-slate-700 mb-4">
              Nous utilisons des cookies essentiels pour le fonctionnement du site :
            </p>
            <ul className="list-disc pl-6 text-slate-700">
              <li><strong>Cookies de session :</strong> Maintenir votre connexion</li>
              <li><strong>Cookies de préférences :</strong> Mémoriser vos choix</li>
            </ul>
            <p className="text-slate-700 mt-4">
              Nous n'utilisons pas de cookies publicitaires ou de tracking tiers.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">8. Sécurité</h2>
            <p className="text-slate-700">
              Nous mettons en œuvre des mesures de sécurité appropriées pour protéger vos données :
              chiffrement SSL/TLS, stockage sécurisé, accès restreint, authentification forte (SSO).
              En cas de violation de données, nous vous en informerons dans les 72 heures conformément au RGPD.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">9. Contact DPO</h2>
            <p className="text-slate-700">
              Pour toute question concernant cette politique ou vos données personnelles :<br />
              <strong>Email :</strong> <a href="mailto:dpo@iaskan.com" className="text-violet-600 hover:underline">dpo@iaskan.com</a><br />
              <strong>Adresse :</strong> IAskan SAS - DPO, 123 Avenue de l'Innovation, 75001 Paris
            </p>
            <p className="text-slate-700 mt-4">
              Vous pouvez également déposer une réclamation auprès de la CNIL : <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" className="text-violet-600 hover:underline">www.cnil.fr</a>
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

export default PrivacyPage;
