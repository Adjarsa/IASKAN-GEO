import { Link } from "react-router-dom";
import { ArrowLeft, Shield, Database, Lock, Eye, Trash2, FileText, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Logo from "@/components/Logo";

const GDPRPage = () => {
  const rights = [
    {
      icon: Eye,
      title: "Droit d'accès",
      description: "Vous pouvez demander une copie de toutes les données personnelles que nous détenons sur vous."
    },
    {
      icon: FileText,
      title: "Droit de rectification",
      description: "Vous pouvez demander la correction de données inexactes ou incomplètes."
    },
    {
      icon: Trash2,
      title: "Droit à l'effacement",
      description: "Vous pouvez demander la suppression de vos données personnelles ('droit à l'oubli')."
    },
    {
      icon: Lock,
      title: "Droit à la limitation",
      description: "Vous pouvez demander de restreindre le traitement de vos données dans certains cas."
    },
    {
      icon: Database,
      title: "Droit à la portabilité",
      description: "Vous pouvez recevoir vos données dans un format structuré et lisible par machine."
    },
    {
      icon: Shield,
      title: "Droit d'opposition",
      description: "Vous pouvez vous opposer au traitement de vos données à des fins de marketing direct."
    }
  ];

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

      {/* Hero */}
      <section className="py-12 px-6 bg-gradient-to-r from-violet-600 to-cyan-600 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 mb-6">
            <Shield className="w-5 h-5" />
            <span className="font-medium">Conformité RGPD</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Protection de vos données personnelles
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            IAskan respecte le Règlement Général sur la Protection des Données (RGPD) 
            et s'engage à protéger votre vie privée.
          </p>
        </div>
      </section>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        
        {/* Introduction */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Notre engagement RGPD</h2>
          <p className="text-slate-700 mb-4">
            Le Règlement Général sur la Protection des Données (RGPD) est un règlement européen 
            qui renforce et unifie la protection des données pour tous les individus au sein de 
            l'Union européenne. Entré en vigueur le 25 mai 2018, il impose des obligations strictes 
            aux entreprises qui traitent des données personnelles.
          </p>
          <p className="text-slate-700">
            Chez IAskan, nous avons intégré les principes du RGPD dès la conception de notre 
            plateforme (Privacy by Design) et nous nous engageons à les respecter dans toutes 
            nos activités.
          </p>
        </section>

        {/* Your Rights */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Vos droits</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {rights.map((right, index) => (
              <Card key={index} className="p-5 flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-violet-100 flex items-center justify-center flex-shrink-0">
                  <right.icon className="w-5 h-5 text-violet-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 mb-1">{right.title}</h3>
                  <p className="text-sm text-slate-600">{right.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Data We Collect */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Données collectées</h2>
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Données d'identification</h3>
                <ul className="list-disc pl-6 text-slate-700 space-y-1">
                  <li>Nom, prénom, email (obligatoires pour la création de compte)</li>
                  <li>Photo de profil (optionnel, via SSO)</li>
                  <li>Nom d'entreprise (optionnel)</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Données d'utilisation</h3>
                <ul className="list-disc pl-6 text-slate-700 space-y-1">
                  <li>Projets créés et marques analysées</li>
                  <li>Historique des analyses et rapports générés</li>
                  <li>Préférences et paramètres de compte</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Données techniques</h3>
                <ul className="list-disc pl-6 text-slate-700 space-y-1">
                  <li>Adresse IP (pour la sécurité et la prévention de la fraude)</li>
                  <li>Empreinte navigateur (pour la protection anti-abus)</li>
                  <li>Cookies de session (strictement nécessaires)</li>
                </ul>
              </div>
            </div>
          </Card>
        </section>

        {/* Legal Basis */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Bases légales du traitement</h2>
          <div className="prose prose-slate max-w-none">
            <p className="text-slate-700 mb-4">Nous traitons vos données sur les bases légales suivantes :</p>
            <ul className="list-disc pl-6 text-slate-700 space-y-2">
              <li><strong>Exécution du contrat :</strong> Le traitement est nécessaire pour vous fournir 
                nos services d'analyse GEO conformément à nos CGV.</li>
              <li><strong>Intérêt légitime :</strong> Pour la prévention de la fraude, la sécurité de 
                notre plateforme et l'amélioration de nos services.</li>
              <li><strong>Consentement :</strong> Pour l'envoi de communications marketing (vous pouvez 
                retirer votre consentement à tout moment).</li>
              <li><strong>Obligation légale :</strong> Pour conserver les données de facturation 
                conformément aux obligations comptables et fiscales.</li>
            </ul>
          </div>
        </section>

        {/* Data Retention */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Durée de conservation</h2>
          <Card className="p-6">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 text-slate-900 font-semibold">Type de données</th>
                  <th className="text-left py-2 text-slate-900 font-semibold">Durée</th>
                </tr>
              </thead>
              <tbody className="text-slate-700">
                <tr className="border-b border-slate-100">
                  <td className="py-3">Données de compte</td>
                  <td className="py-3">Durée de l'abonnement + 3 ans</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3">Données d'analyse (projets, rapports)</td>
                  <td className="py-3">2 ans après dernière utilisation</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3">Logs de sécurité</td>
                  <td className="py-3">1 an</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3">Données de facturation</td>
                  <td className="py-3">10 ans (obligation légale)</td>
                </tr>
                <tr>
                  <td className="py-3">Données anti-fraude</td>
                  <td className="py-3">6 mois</td>
                </tr>
              </tbody>
            </table>
          </Card>
        </section>

        {/* Security */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Sécurité des données</h2>
          <p className="text-slate-700 mb-4">
            Nous mettons en œuvre des mesures techniques et organisationnelles appropriées pour 
            protéger vos données :
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="p-4 bg-slate-50">
              <h4 className="font-semibold text-slate-900 mb-2">Mesures techniques</h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Chiffrement SSL/TLS en transit</li>
                <li>• Chiffrement des données sensibles au repos</li>
                <li>• Authentification sécurisée (SSO, sessions)</li>
                <li>• Pare-feu et protection DDoS</li>
              </ul>
            </Card>
            <Card className="p-4 bg-slate-50">
              <h4 className="font-semibold text-slate-900 mb-2">Mesures organisationnelles</h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Accès restreint aux données (besoin de savoir)</li>
                <li>• Formation du personnel au RGPD</li>
                <li>• Procédures de gestion des incidents</li>
                <li>• Audits de sécurité réguliers</li>
              </ul>
            </Card>
          </div>
        </section>

        {/* Third Parties */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Sous-traitants</h2>
          <p className="text-slate-700 mb-4">
            Nous faisons appel à des sous-traitants conformes au RGPD pour certains traitements :
          </p>
          <Card className="p-6">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 text-slate-900 font-semibold">Sous-traitant</th>
                  <th className="text-left py-2 text-slate-900 font-semibold">Finalité</th>
                  <th className="text-left py-2 text-slate-900 font-semibold">Localisation</th>
                </tr>
              </thead>
              <tbody className="text-slate-700">
                <tr className="border-b border-slate-100">
                  <td className="py-3">MongoDB Atlas</td>
                  <td className="py-3">Hébergement base de données</td>
                  <td className="py-3">UE (Irlande)</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3">Stripe</td>
                  <td className="py-3">Traitement des paiements</td>
                  <td className="py-3">UE / USA (SCCs)</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-3">Resend</td>
                  <td className="py-3">Envoi d'emails transactionnels</td>
                  <td className="py-3">USA (SCCs)</td>
                </tr>
                <tr>
                  <td className="py-3">OpenAI, Anthropic, Google</td>
                  <td className="py-3">Analyse IA (données anonymisées)</td>
                  <td className="py-3">USA (SCCs)</td>
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-slate-500 mt-4">
              SCCs = Standard Contractual Clauses (Clauses Contractuelles Types) pour les transferts hors UE
            </p>
          </Card>
        </section>

        {/* Exercise Your Rights */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Exercer vos droits</h2>
          <Card className="p-6 bg-violet-50 border-violet-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center flex-shrink-0">
                <Mail className="w-6 h-6 text-violet-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Délégué à la Protection des Données (DPO)</h3>
                <p className="text-slate-700 mb-4">
                  Pour exercer vos droits ou pour toute question relative à la protection de vos données, 
                  vous pouvez contacter notre DPO :
                </p>
                <ul className="text-slate-700 space-y-1">
                  <li><strong>Email :</strong> <a href="mailto:dpo@iaskan.com" className="text-violet-600 hover:underline">dpo@iaskan.com</a></li>
                  <li><strong>Adresse :</strong> IAskan SAS - DPO, 123 Avenue de l'Innovation, 75001 Paris</li>
                </ul>
                <p className="text-sm text-slate-600 mt-4">
                  Nous répondrons à votre demande dans un délai de 30 jours maximum.
                </p>
              </div>
            </div>
          </Card>
        </section>

        {/* CNIL */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Réclamation</h2>
          <p className="text-slate-700">
            Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation 
            auprès de l'autorité de contrôle compétente :
          </p>
          <Card className="p-6 mt-4">
            <h3 className="font-semibold text-slate-900 mb-2">CNIL - Commission Nationale de l'Informatique et des Libertés</h3>
            <ul className="text-slate-700 space-y-1">
              <li><strong>Site web :</strong> <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" className="text-violet-600 hover:underline">www.cnil.fr</a></li>
              <li><strong>Adresse :</strong> 3 Place de Fontenoy, TSA 80715, 75334 Paris Cedex 07</li>
              <li><strong>Téléphone :</strong> 01 53 73 22 22</li>
            </ul>
          </Card>
        </section>

        <p className="text-sm text-slate-500 mt-12">
          Dernière mise à jour : {new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}
        </p>
      </main>
    </div>
  );
};

export default GDPRPage;
