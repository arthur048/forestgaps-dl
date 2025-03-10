# Interface CLI pour le prétraitement
"""
Interface en ligne de commande pour le prétraitement des données ForestGaps-DL.

Ce module fournit une interface en ligne de commande pour les fonctionnalités
de prétraitement des données du workflow ForestGaps-DL.
"""

import os
import argparse
import logging
from typing import Dict, List, Optional, Any

from config import ConfigManager
from environment import get_environment
from utils.errors import ErrorHandler


def setup_parser() -> argparse.ArgumentParser:
    """
    Configure le parseur d'arguments pour l'interface CLI de prétraitement.
    
    Returns:
        argparse.ArgumentParser: Parseur d'arguments configuré.
    """
    parser = argparse.ArgumentParser(
        description="ForestGaps-DL - Prétraitement des données",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Arguments généraux
    parser.add_argument('--config', type=str, default='config/defaults/preprocessing.yaml',
                        help='Chemin vers le fichier de configuration')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Niveau de journalisation')
    parser.add_argument('--output-dir', type=str, help='Répertoire de sortie (remplace la valeur de la configuration)')
    
    # Sous-commandes
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Commande: align
    align_parser = subparsers.add_parser('align', help='Aligner les rasters DSM et CHM')
    align_parser.add_argument('--dsm', type=str, required=True, help='Chemin vers le fichier DSM')
    align_parser.add_argument('--chm', type=str, required=True, help='Chemin vers le fichier CHM')
    align_parser.add_argument('--resampling', type=str, default='bilinear',
                             choices=['nearest', 'bilinear', 'cubic', 'lanczos'],
                             help='Méthode de rééchantillonnage')
    
    # Commande: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyser les rasters')
    analyze_parser.add_argument('--input', type=str, required=True, help='Chemin vers le fichier raster à analyser')
    analyze_parser.add_argument('--save-stats', action='store_true', help='Sauvegarder les statistiques')
    
    # Commande: generate-tiles
    tiles_parser = subparsers.add_parser('generate-tiles', help='Générer des tuiles à partir des rasters')
    tiles_parser.add_argument('--dsm', type=str, required=True, help='Chemin vers le fichier DSM')
    tiles_parser.add_argument('--chm', type=str, help='Chemin vers le fichier CHM (optionnel)')
    tiles_parser.add_argument('--tile-size', type=int, default=256, help='Taille des tuiles en pixels')
    tiles_parser.add_argument('--overlap', type=float, default=0.0, help='Chevauchement entre les tuiles (0.0 à 1.0)')
    tiles_parser.add_argument('--min-valid-ratio', type=float, default=0.7,
                             help='Ratio minimum de pixels valides pour conserver une tuile')
    
    # Commande: generate-masks
    masks_parser = subparsers.add_parser('generate-masks', help='Générer des masques de trouées')
    masks_parser.add_argument('--chm', type=str, required=True, help='Chemin vers le fichier CHM')
    masks_parser.add_argument('--thresholds', type=str, required=True,
                             help='Liste de seuils de hauteur séparés par des virgules (ex: 10,15,20)')
    
    return parser


def run_align_command(args: argparse.Namespace, config: Dict, error_handler: ErrorHandler) -> None:
    """
    Exécute la commande d'alignement des rasters.
    
    Args:
        args: Arguments de la ligne de commande.
        config: Configuration.
        error_handler: Gestionnaire d'erreurs.
    """
    try:
        logging.info(f"Alignement des rasters: {args.dsm} et {args.chm}")
        
        # Déterminer le répertoire de sortie
        output_dir = args.output_dir or config.get('output_dir', 'output/aligned')
        os.makedirs(output_dir, exist_ok=True)
        
        # Déterminer les chemins de sortie
        dsm_filename = os.path.basename(args.dsm)
        chm_filename = os.path.basename(args.chm)
        aligned_dsm_path = os.path.join(output_dir, f"aligned_{dsm_filename}")
        aligned_chm_path = os.path.join(output_dir, f"aligned_{chm_filename}")
        
        # Aligner les rasters
        from data.preprocessing.alignment import align_rasters
        align_rasters(args.dsm, args.chm, aligned_dsm_path, aligned_chm_path, args.resampling)
        
        logging.info(f"Rasters alignés sauvegardés dans {output_dir}")
    except Exception as e:
        error_handler.handle(e, context={'command': 'align', 'args': vars(args)})
        logging.error(f"Erreur lors de l'alignement des rasters: {str(e)}")


def run_analyze_command(args: argparse.Namespace, config: Dict, error_handler: ErrorHandler) -> None:
    """
    Exécute la commande d'analyse des rasters.
    
    Args:
        args: Arguments de la ligne de commande.
        config: Configuration.
        error_handler: Gestionnaire d'erreurs.
    """
    try:
        logging.info(f"Analyse du raster: {args.input}")
        
        # Analyser le raster
        from data.preprocessing.analysis import calculate_raster_statistics
        stats = calculate_raster_statistics(args.input)
        
        # Afficher les statistiques
        logging.info("Statistiques du raster:")
        for key, value in stats.items():
            logging.info(f"  {key}: {value}")
        
        # Sauvegarder les statistiques si demandé
        if args.save_stats:
            output_dir = args.output_dir or config.get('output_dir', 'output/stats')
            os.makedirs(output_dir, exist_ok=True)
            
            filename = os.path.basename(args.input).split('.')[0]
            stats_path = os.path.join(output_dir, f"{filename}_stats.json")
            
            from utils.io.serialization import save_json
            save_json(stats, stats_path)
            logging.info(f"Statistiques sauvegardées dans {stats_path}")
    except Exception as e:
        error_handler.handle(e, context={'command': 'analyze', 'args': vars(args)})
        logging.error(f"Erreur lors de l'analyse du raster: {str(e)}")


def run_generate_tiles_command(args: argparse.Namespace, config: Dict, error_handler: ErrorHandler) -> None:
    """
    Exécute la commande de génération de tuiles.
    
    Args:
        args: Arguments de la ligne de commande.
        config: Configuration.
        error_handler: Gestionnaire d'erreurs.
    """
    try:
        logging.info(f"Génération de tuiles à partir de: {args.dsm}")
        
        # Déterminer le répertoire de sortie
        output_dir = args.output_dir or config.get('output_dir', 'output/tiles')
        os.makedirs(output_dir, exist_ok=True)
        
        # Générer les tuiles
        from data.generation.tiling import create_tiles_from_raster
        tiles_info = create_tiles_from_raster(
            args.dsm,
            tile_size=args.tile_size,
            overlap=args.overlap,
            output_dir=output_dir,
            min_valid_ratio=args.min_valid_ratio
        )
        
        # Générer les tuiles CHM si spécifié
        if args.chm:
            chm_tiles_info = create_tiles_from_raster(
                args.chm,
                tile_size=args.tile_size,
                overlap=args.overlap,
                output_dir=output_dir,
                min_valid_ratio=args.min_valid_ratio
            )
            
            # Sauvegarder les informations sur les tuiles
            tiles_metadata = {
                'dsm_tiles': tiles_info,
                'chm_tiles': chm_tiles_info,
                'tile_size': args.tile_size,
                'overlap': args.overlap
            }
        else:
            # Sauvegarder les informations sur les tuiles
            tiles_metadata = {
                'dsm_tiles': tiles_info,
                'tile_size': args.tile_size,
                'overlap': args.overlap
            }
        
        # Sauvegarder les métadonnées
        from utils.io.serialization import save_json
        metadata_path = os.path.join(output_dir, 'tiles_metadata.json')
        save_json(tiles_metadata, metadata_path)
        
        logging.info(f"Tuiles générées: {len(tiles_info)}")
        logging.info(f"Métadonnées sauvegardées dans {metadata_path}")
    except Exception as e:
        error_handler.handle(e, context={'command': 'generate-tiles', 'args': vars(args)})
        logging.error(f"Erreur lors de la génération des tuiles: {str(e)}")


def run_generate_masks_command(args: argparse.Namespace, config: Dict, error_handler: ErrorHandler) -> None:
    """
    Exécute la commande de génération de masques.
    
    Args:
        args: Arguments de la ligne de commande.
        config: Configuration.
        error_handler: Gestionnaire d'erreurs.
    """
    try:
        # Convertir la chaîne de seuils en liste de nombres
        thresholds = [float(t) for t in args.thresholds.split(',')]
        logging.info(f"Génération de masques pour les seuils: {thresholds}")
        
        # Déterminer le répertoire de sortie
        output_dir = args.output_dir or config.get('output_dir', 'output/masks')
        os.makedirs(output_dir, exist_ok=True)
        
        # Générer les masques pour chaque seuil
        from data.generation.masks import create_gap_mask
        mask_paths = {}
        for threshold in thresholds:
            mask_filename = f"mask_{int(threshold)}m.tif"
            mask_path = os.path.join(output_dir, mask_filename)
            
            create_gap_mask(args.chm, threshold, mask_path)
            mask_paths[threshold] = mask_path
            
            logging.info(f"Masque généré pour le seuil {threshold}m: {mask_path}")
        
        # Sauvegarder les métadonnées
        from utils.io.serialization import save_json
        metadata_path = os.path.join(output_dir, 'masks_metadata.json')
        save_json({
            'chm_path': args.chm,
            'thresholds': thresholds,
            'mask_paths': mask_paths
        }, metadata_path)
        
        logging.info(f"Métadonnées sauvegardées dans {metadata_path}")
    except Exception as e:
        error_handler.handle(e, context={'command': 'generate-masks', 'args': vars(args)})
        logging.error(f"Erreur lors de la génération des masques: {str(e)}")


def main() -> None:
    """Point d'entrée principal pour l'interface CLI de prétraitement."""
    # Configurer le parseur d'arguments
    parser = setup_parser()
    args = parser.parse_args()
    
    # Configurer la journalisation
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Charger la configuration
    config_manager = ConfigManager()
    config = config_manager.load_config(args.config)
    
    # Initialiser le gestionnaire d'erreurs
    error_handler = ErrorHandler(
        log_file=config.get('error_log', 'logs/preprocessing_errors.log'),
        verbose=True
    )
    
    # Initialiser l'environnement
    env = get_environment()
    env.setup()
    
    # Exécuter la commande appropriée
    if args.command == 'align':
        run_align_command(args, config, error_handler)
    elif args.command == 'analyze':
        run_analyze_command(args, config, error_handler)
    elif args.command == 'generate-tiles':
        run_generate_tiles_command(args, config, error_handler)
    elif args.command == 'generate-masks':
        run_generate_masks_command(args, config, error_handler)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
