import PropTypes from 'prop-types';
import SidebarMenu from '../../components/SidebarMenu/SidebarMenu';
import { useMainNavigation } from '../../hooks/useMainNavigation';
import styles from './MainLayout.module.css';

function MainLayout({ user, onLogout }) {
  const { menuItems, activeItem, selectRoute, activeContentRenderer, placeholderContent } =
    useMainNavigation(user?.permissions);

  const content = activeContentRenderer ? activeContentRenderer() : null;

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.branding}>
          <div className={styles.brandBadge}>FC</div>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>Florería Carlitos</span>
            <span className={styles.brandSubtitle}>Panel administrativo</span>
          </div>
        </div>

        <div className={styles.userBlock}>
          <span className={styles.userName}>{user?.full_name ?? 'Usuario sin nombre'}</span>
          <span className={styles.userRole}>{user?.role ?? 'Colaborador'}</span>
        </div>

        <SidebarMenu items={menuItems} activeItemId={activeItem?.id} onSelect={selectRoute} />

        {typeof onLogout === 'function' ? (
          <button type="button" className={styles.logoutButton} onClick={onLogout}>
            Cerrar sesión
          </button>
        ) : null}
      </aside>

      <section className={styles.contentArea}>
        <header className={styles.contentHeader}>
          <div>
            <h1 className={styles.contentTitle}>{activeItem?.label}</h1>
            <p className={styles.contentDescription}>{activeItem?.description}</p>
          </div>
          <div className={styles.contentStatus}>
            <span className={styles.statusPill}>Versión preliminar</span>
          </div>
        </header>

        <div className={styles.contentBody}>
          {content ?? (
            <div className={styles.placeholder}>
              <h2>{placeholderContent?.title}</h2>
              <p>{placeholderContent?.description}</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

MainLayout.propTypes = {
  user: PropTypes.shape({
    full_name: PropTypes.string,
    role: PropTypes.string,
    permissions: PropTypes.arrayOf(PropTypes.string),
  }),
  onLogout: PropTypes.func,
};

MainLayout.defaultProps = {
  user: null,
  onLogout: undefined,
};

export default MainLayout;
