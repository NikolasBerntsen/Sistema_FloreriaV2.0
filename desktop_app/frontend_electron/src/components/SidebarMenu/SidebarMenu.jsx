import PropTypes from 'prop-types';
import styles from './SidebarMenu.module.css';

function SidebarMenuItem({ item, isActive, onSelect }) {
  const handleClick = () => {
    if (!item.isAllowed) {
      return;
    }
    onSelect(item.id);
  };

  return (
    <button
      type="button"
      className={[
        styles.menuItem,
        isActive ? styles.menuItemActive : undefined,
        !item.isAllowed ? styles.menuItemDisabled : undefined,
      ]
        .filter(Boolean)
        .join(' ')}
      onClick={handleClick}
      aria-pressed={isActive}
      aria-disabled={!item.isAllowed}
    >
      <span className={styles.menuItemLabel}>{item.label}</span>
      {item.description && <span className={styles.menuItemHint}>{item.description}</span>}
      {!item.isAllowed && <span className={styles.menuItemPermission}>Sin permiso</span>}
    </button>
  );
}

SidebarMenuItem.propTypes = {
  item: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    description: PropTypes.string,
    isAllowed: PropTypes.bool,
  }).isRequired,
  isActive: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
};

function SidebarMenu({ items, activeItemId, onSelect }) {
  return (
    <nav className={styles.menu} aria-label="Navegación principal">
      {items.map((item) => (
        <SidebarMenuItem
          key={item.id}
          item={item}
          isActive={activeItemId === item.id}
          onSelect={onSelect}
        />
      ))}
    </nav>
  );
}

SidebarMenu.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      description: PropTypes.string,
      isAllowed: PropTypes.bool,
    }).isRequired,
  ).isRequired,
  activeItemId: PropTypes.string,
  onSelect: PropTypes.func.isRequired,
};

SidebarMenu.defaultProps = {
  activeItemId: undefined,
};

export default SidebarMenu;
