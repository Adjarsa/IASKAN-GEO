import { Link } from "react-router-dom";
import { ArrowLeft, Target, Users, Lightbulb, Shield, TrendingUp, Award } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Logo from "@/components/Logo";

const AboutPage = () => {
  const values = [
    {
      icon: Target,
      title: "Précision",
      description: "Des analyses rigoureuses basées sur une méthodologie scientifique multi-IA et multi-runs."
    },
    {
      icon: Lightbulb,
      title: "Innovation",
      description: "Pionniers du GEO, nous développons des indices et métriques exclusifs pour l'optimisation IA."
    },
    {
      icon: Shield,
      title: "Transparence",
      description: "Méthodologie documentée, résultats reproductibles, pas de boîte noire."
    },
    {
      icon: Users,
      title: "Accompagnement",
      description: "Au-delà des données, nous guidons nos clients vers des actions concrètes et mesurables."
    }
  ];

  const milestones = [
    { year: "2024", event: "Création d'IAskan", description: "Lancement de la première plateforme GEO en France" },
    { year: "2024", event: "IAskan Verified Protocol™", description: "Développement de notre méthodologie brevetée" },
    { year: "2025", event: "Score R.A.T.E.™", description: "Introduction du premier framework de scoring GEO" },
    { year: "2025", event: "Expansion européenne", description: "Déploiement multilingue et équipes locales" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="border-b border-slate-100 bg-white/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
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
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
            Pionniers de l'optimisation pour les IA génératives
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            IAskan aide les entreprises à comprendre et améliorer leur visibilité dans les réponses 
            générées par les intelligences artificielles comme ChatGPT, Claude et Gemini.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16 px-6 bg-gradient-to-r from-violet-600 to-cyan-600">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-3xl font-bold mb-6">Notre Mission</h2>
          <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
            Démocratiser l'accès à l'analyse GEO en offrant des outils puissants, compréhensibles 
            et actionnables à toutes les entreprises qui souhaitent exister dans le nouveau monde 
            des moteurs de réponse IA.
          </p>
        </div>
      </section>

      {/* Problem / Solution */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 mb-6">Le défi du GEO</h2>
              <p className="text-slate-600 mb-4">
                Avec l'adoption massive des assistants IA, les consommateurs changent leur façon 
                de découvrir et choisir les produits et services. Ils ne cliquent plus sur des liens, 
                ils demandent directement des recommandations.
              </p>
              <p className="text-slate-600 mb-4">
                <strong>Le problème :</strong> Les entreprises n'ont aucune visibilité sur comment 
                les IA parlent d'elles. Sont-elles mentionnées ? Recommandées ? Comparées favorablement 
                à la concurrence ?
              </p>
              <p className="text-slate-600">
                <strong>Notre solution :</strong> IAskan analyse systématiquement votre présence 
                dans les réponses IA et vous donne les clés pour l'améliorer.
              </p>
            </div>
            <div className="bg-slate-900 rounded-2xl p-8 text-white">
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="w-8 h-8 text-cyan-400" />
                <span className="text-2xl font-bold">+340%</span>
              </div>
              <p className="text-slate-300 mb-6">
                Croissance des requêtes utilisateurs sur les assistants IA en 2024
              </p>
              <div className="flex items-center gap-3 mb-6">
                <Award className="w-8 h-8 text-violet-400" />
                <span className="text-2xl font-bold">73%</span>
              </div>
              <p className="text-slate-300">
                Des utilisateurs font confiance aux recommandations IA pour leurs achats
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">Nos Valeurs</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <Card key={index} className="p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-100 to-cyan-100 flex items-center justify-center mx-auto mb-4">
                  <value.icon className="w-7 h-7 text-violet-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{value.title}</h3>
                <p className="text-slate-600 text-sm">{value.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">Notre Histoire</h2>
          <div className="space-y-8">
            {milestones.map((milestone, index) => (
              <div key={index} className="flex gap-6 items-start">
                <div className="flex-shrink-0 w-20 text-right">
                  <span className="text-lg font-bold text-violet-600">{milestone.year}</span>
                </div>
                <div className="flex-shrink-0 w-4 h-4 mt-1.5 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500" />
                <div>
                  <h3 className="font-semibold text-slate-900">{milestone.event}</h3>
                  <p className="text-slate-600">{milestone.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-6">L'équipe</h2>
          <p className="text-slate-600 mb-8 max-w-2xl mx-auto">
            IAskan est fondée par une équipe passionnée combinant expertise en IA, SEO, 
            et développement produit. Nous avons travaillé dans les plus grandes entreprises 
            tech et agences digitales avant de créer IAskan.
          </p>
          <Link to="/contact">
            <Button className="bg-gradient-to-r from-violet-600 to-cyan-600">
              Nous rejoindre
            </Button>
          </Link>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <Card className="p-12 bg-gradient-to-r from-violet-600 to-cyan-600 text-center text-white">
            <h2 className="text-3xl font-bold mb-4">Prêt à optimiser votre visibilité GEO ?</h2>
            <p className="text-white/80 mb-8 max-w-xl mx-auto">
              Découvrez comment les IA parlent de votre marque et obtenez des recommandations 
              personnalisées pour améliorer votre positionnement.
            </p>
            <Link to="/login">
              <Button size="lg" className="bg-white text-violet-600 hover:bg-slate-100">
                Commencer gratuitement
              </Button>
            </Link>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;
