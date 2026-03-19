"""
Preflight check for migration 0029 - predicts task_type restoration results.

Usage:
    python manage.py preflight_template_tasktypes

This command checks what migration 0029 would do without actually making changes.
Run this on production before deploying to verify all templates will be matched.
"""

from django.core.management.base import BaseCommand
from core.models import TaskType, TaskTemplate


class Command(BaseCommand):
    help = 'Preflight check: Preview task_type restoration without making changes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each template',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually apply the fixes (use with caution!)',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        should_fix = options['fix']
        
        self.stdout.write("=" * 70)
        if should_fix:
            self.stdout.write(self.style.WARNING("APPLYING FIXES - THIS WILL MODIFY DATA"))
        else:
            self.stdout.write(self.style.NOTICE("PREFLIGHT CHECK (Dry Run - No Changes)"))
        self.stdout.write("=" * 70)
        
        # Check available TaskTypes
        self.stdout.write("\n1. Available TaskTypes:")
        task_types = {}
        for tt in TaskType.objects.all().order_by('code'):
            task_types[tt.code] = tt.id
            self.stdout.write(f"   - '{tt.code}' ({tt.name})")
        
        if not task_types:
            self.stdout.write(self.style.ERROR("   [WARN]  No TaskTypes found! Migration cannot proceed."))
            return
        
        # Check templates needing updates
        self.stdout.write("\n2. Templates needing task_type assignment:")
        templates = TaskTemplate.objects.filter(task_type__isnull=True).order_by('name')
        total_count = templates.count()
        self.stdout.write(f"   Count: {total_count}")
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("   [OK] All templates already have task_types assigned!"))
            return
        
        if verbose:
            for t in templates:
                self.stdout.write(f"   - '{t.name}' (assignee: {t.assignee_type})")
        
        # Predict what will happen
        self.stdout.write("\n3. Predicted mappings:")
        
        keyword_mappings = [
            (['weed', 'invasive removal', 'wattle', 'brush', 'removal', 'stabilization', 'pathway', 'biological', 'seed collection'], 'weeding'),
            (['litter', 'clean', 'trash', 'debris', 'dumping', 'drain', 'quality monitoring'], 'litter_run'),
            (['planting', 'plant tree', 'tree planting', 'wetland', 'pollinator', 'riparian', 'garden'], 'planting'),
            (['admin', 'fundraising', 'media', 'meeting', 'outreach', 'planning', 'reporting', 'survey', 'committee', 'intern', 'workshop'], 'admin'),
        ]
        
        original_mappings = {
            'Emergency Litter Cleanup': 'litter_run',
            'River Bank Stabilization': 'weeding',
            'Native Tree Planting': 'planting',
            'Water Quality Monitoring': 'litter_run',
            'Community Cleanup Day': 'litter_run',
            'Invasive Plant Removal - Wattle': 'weeding',
            'Wetland Planting': 'planting',
            'Debris Removal - Large Items': 'litter_run',
            'Pathway Maintenance': 'weeding',
            'Pollinator Garden Planting': 'planting',
            'Storm Drain Clearing': 'litter_run',
            'Biological Control Monitoring': 'weeding',
            'Riparian Buffer Planting': 'planting',
            'Illegal Dumping Site Cleanup': 'litter_run',
            'Seed Collection': 'weeding',
            'Educational Planting Day': 'planting',
        }
        
        matched = 0
        unmatched = 0
        updates_to_make = []
        
        for template in templates:
            name = template.name
            task_type_code = None
            match_type = None
            
            # Exact match
            if name in original_mappings:
                task_type_code = original_mappings[name]
                match_type = 'exact'
            else:
                # Keyword match
                name_lower = name.lower()
                for keywords, code in keyword_mappings:
                    if any(keyword in name_lower for keyword in keywords):
                        task_type_code = code
                        match_type = 'keyword'
                        break
            
            if task_type_code and task_type_code in task_types:
                updates_to_make.append((template, task_type_code, match_type))
                if verbose:
                    self.stdout.write(f"   [OK] '{name}' -> {task_type_code} ({match_type})")
                matched += 1
            else:
                if verbose:
                    reason = f"unknown code '{task_type_code}'" if task_type_code else "no keyword match"
                    self.stdout.write(self.style.WARNING(f"   [WARN]  '{name}' -> NO MATCH ({reason})"))
                unmatched += 1
        
        if not verbose and matched > 0:
            self.stdout.write(f"   [OK] {matched} templates will be matched")
        if unmatched > 0:
            self.stdout.write(self.style.WARNING(f"   [WARN]  {unmatched} templates won't be matched (use --verbose to see details)"))
        
        # Summary
        self.stdout.write("\n4. Summary:")
        self.stdout.write(f"   Total templates needing fix: {total_count}")
        self.stdout.write(f"   Will be matched: {matched}")
        self.stdout.write(f"   Will remain NULL: {unmatched}")
        
        # Breakdown by type
        if updates_to_make:
            from collections import Counter
            type_counts = Counter(code for _, code, _ in updates_to_make)
            self.stdout.write("\n5. Breakdown by task type:")
            for code, count in sorted(type_counts.items()):
                self.stdout.write(f"   - {code}: {count} templates")
        
        self.stdout.write("\n" + "=" * 70)
        
        if should_fix:
            # Actually apply the fixes
            self.stdout.write(self.style.WARNING("APPLYING FIXES..."))
            applied = 0
            for template, task_type_code, match_type in updates_to_make:
                task_type_id = task_types[task_type_code]
                template.task_type_id = task_type_id
                template.save(update_fields=['task_type'])
                applied += 1
                if verbose:
                    self.stdout.write(f"   Fixed: '{template.name}' -> {task_type_code}")
            self.stdout.write(self.style.SUCCESS(f"[OK] Applied {applied} fixes"))
        else:
            # Just report
            if unmatched == 0:
                self.stdout.write(self.style.SUCCESS("SAFE TO PROCEED"))
                self.stdout.write("\nRun migration with: python manage.py migrate core 0029")
                self.stdout.write("Or apply immediately: python manage.py preflight_template_tasktypes --fix")
            else:
                self.stdout.write(self.style.WARNING(f"REVIEW NEEDED: {unmatched} templates won't be matched"))
                self.stdout.write("\nThese templates will remain 'Uncategorized'.")
                self.stdout.write("Consider adding them to the migration's keyword_mappings.")
        
        self.stdout.write("=" * 70)
