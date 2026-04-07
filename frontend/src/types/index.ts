export interface User {
  id: string;
  nom: string;
  email: string;
  role: 'ADMIN' | 'ANALYSTE';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Rapport {
  id: string;
  nom: string;
  format: 'pdf' | 'docx' | 'xlsx';
  statut: 'en_attente' | 'en_cours' | 'termine' | 'erreur';
  created_at: string;
}

export interface Analyse {
  id: string;
  rapport_id: string;
  resume_executif: string | null;
  score_maturite: number | null;
  statut: 'en_cours' | 'termine' | 'erreur';
  created_at: string;
}

export interface Risque {
  id: string;
  libelle: string;
  description: string | null;
  categorie: 'CYBER' | 'OPERATIONNEL' | 'LEGAL' | 'FINANCIER' | 'RH';
  probabilite: number;
  impact: number;
  score_risque: number;
  severite: 'CRITIQUE' | 'ELEVE' | 'MOYEN' | 'FAIBLE';
  section_source: string | null;
}

export interface Conformite {
  id: string;
  referentiel: 'ISO27001' | 'RGPD' | 'LOI0908';
  domaine: string | null;
  statut: 'CONFORME' | 'NON_CONFORME' | 'PARTIEL';
  ecart: string | null;
  taux_conformite: number;
}

export interface Recommandation {
  id: string;
  libelle: string;
  description: string | null;
  priorite: 'CRITIQUE' | 'HAUTE' | 'MOYENNE' | 'FAIBLE';
  type_action: 'QUICK_WIN' | 'LONG_TERME';
  effort_estime: 'FAIBLE' | 'MOYEN' | 'ELEVE';
  statut: 'A_FAIRE' | 'EN_COURS' | 'CLOTURE';
  created_at: string;
  risque_id: string | null;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}
